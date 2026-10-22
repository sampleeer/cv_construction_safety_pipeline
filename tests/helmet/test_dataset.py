import io
import json
import zipfile

import pytest
import yaml
from PIL import Image

from src.helmet.dataset import convert_labels, prepare


def archive_fixture(tmp_path, duplicate=False):
    archive = tmp_path / 'ppe.zip'
    with zipfile.ZipFile(archive, 'w') as bundle:
        for index, split in enumerate(('train', 'val', 'test')):
            stream = io.BytesIO()
            Image.new('RGB', (20, 20), (index * 40, 10, 20)).save(stream, format='PNG')
            bundle.writestr(f'images/{split}/sample.png', stream.getvalue())
            bundle.writestr(f'labels/{split}/sample.txt', '0 .5 .5 .2 .2\n7 .4 .4 .1 .1\n6 .5 .5 .8 .8\n5 .1 .1 .1 .1\n')
        if duplicate:
            bundle.writestr('images/train/duplicate.png', stream.getvalue())
            bundle.writestr('labels/train/duplicate.txt', '7 .5 .5 .2 .2\n')
    config = tmp_path / 'params.yaml'
    config.write_text(yaml.safe_dump({'profile': 'test', 'seed': 42, 'max_train': 0, 'max_val': 0, 'max_test': 0}))
    return archive, config


def test_class_mapping_and_label_validation():
    assert convert_labels('0 .5 .5 .2 .2\n7 .4 .4 .1 .1\n6 .5 .5 .8 .8') == [
        '0 .5 .5 .2 .2', '1 .4 .4 .1 .1', '2 .5 .5 .8 .8']
    for text in ('0 1 2', '12 .5 .5 .1 .1', '7 nan .5 .1 .1', '7 .5 .5 0 .1'):
        with pytest.raises(ValueError):
            convert_labels(text)


def test_prepare_preserves_splits_and_removes_exact_cross_split_duplicates(tmp_path):
    archive, config = archive_fixture(tmp_path, duplicate=True)
    output = tmp_path / 'prepared'
    manifest = prepare(archive, output, config)
    assert manifest['splits']['train']['duplicates_removed'] == 1
    assert manifest['splits']['train']['objects'] == {'helmet': 1, 'no_helmet': 1, 'person': 1}
    assert (output / 'labels/test/sample.txt').read_text().splitlines()[1].startswith('1 ')
    assert 'path' not in yaml.safe_load((output / 'data.yaml').read_text())
    second = prepare(archive, output, config)
    assert second['fingerprint'] == manifest['fingerprint']
    assert json.loads((output / 'manifest.json').read_text())['source_url']


def test_output_not_owned_by_pipeline_is_protected(tmp_path):
    archive, config = archive_fixture(tmp_path)
    output = tmp_path / 'user-data'
    output.mkdir()
    with pytest.raises(FileExistsError):
        prepare(archive, output, config)


def test_unsafe_archive_is_rejected(tmp_path):
    archive, config = archive_fixture(tmp_path)
    with zipfile.ZipFile(archive, 'a') as bundle:
        bundle.writestr('../outside.txt', 'bad')
    with pytest.raises(ValueError, match='Unsafe'):
        prepare(archive, tmp_path / 'prepared', config)
    assert not (tmp_path / 'outside.txt').exists()


def rewrite_archive(archive, changes):
    with zipfile.ZipFile(archive) as bundle:
        entries = {name: bundle.read(name) for name in bundle.namelist()}
    for name, value in changes.items():
        if value is None:
            entries.pop(name, None)
        else:
            entries[name] = value
    with zipfile.ZipFile(archive, 'w') as bundle:
        for name, value in entries.items():
            bundle.writestr(name, value)


def test_demo_prioritizes_no_helmet_only_in_train_and_respects_limit(tmp_path):
    archive, config = archive_fixture(tmp_path)
    stream = io.BytesIO()
    Image.new('RGB', (20, 20), (200, 30, 40)).save(stream, format='PNG')
    rewrite_archive(archive, {
        'labels/train/sample.txt': '0 .5 .5 .2 .2\n',
        'images/train/violation.png': stream.getvalue(),
        'labels/train/violation.txt': '7 .5 .5 .2 .2\n',
    })
    settings = yaml.safe_load(config.read_text())
    settings.update(max_train=1, prioritize_no_helmet=True)
    config.write_text(yaml.safe_dump(settings))
    output = tmp_path / 'prepared'
    manifest = prepare(archive, output, config)
    assert manifest['splits']['train']['images'] == 1
    assert manifest['splits']['train']['samples'][0]['image'] == 'violation.png'
    assert manifest['splits']['train']['objects']['no_helmet'] == 1
    assert manifest['splits']['val']['samples'][0]['image'] == 'sample.png'


@pytest.mark.parametrize(('changes', 'error', 'message'), [
    ({'labels/train/sample.txt': None}, FileNotFoundError, 'Missing annotation'),
    ({'images/train/sample.png': None}, ValueError, 'Expected exactly one official'),
    ({'images/val/sample.png': None}, ValueError, 'Empty split'),
    ({'images/train/sample.png': b'not an image'}, OSError, 'cannot identify image'),
])
def test_bad_source_does_not_replace_previously_prepared_dataset(tmp_path, changes, error, message):
    archive, config = archive_fixture(tmp_path)
    output = tmp_path / 'prepared'
    prepare(archive, output, config)
    original = (output / 'manifest.json').read_bytes()
    rewrite_archive(archive, changes)
    with pytest.raises(error, match=message):
        prepare(archive, output, config)
    assert (output / 'manifest.json').read_bytes() == original
    assert (output / 'images/train/sample.png').exists()


def test_dataset_cli_writes_dataset_and_reports_split_sizes(tmp_path, monkeypatch, capsys):
    from src.helmet.dataset import main

    archive, config = archive_fixture(tmp_path)
    output = tmp_path / 'prepared'
    monkeypatch.setattr('sys.argv', ['dataset', '--archive', str(archive), '--output', str(output),
                                    '--config', str(config)])
    main()
    assert json.loads(capsys.readouterr().out) == {'test': 1, 'val': 1, 'train': 1}
    assert (output / 'data.yaml').is_file()
