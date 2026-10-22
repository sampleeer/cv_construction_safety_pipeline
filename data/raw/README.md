# Исходные данные HelmetWatch

Источник — Construction-PPE. Скачайте архив командой из корня проекта:

```bash
python -m src.helmet.download
```

Архив сохраняется в `data/raw/ppe/construction-ppe.zip` и не включается в Git.
Стадия `prepare` в `dvc repro` создаёт трёхклассовый датасет в `data/helmet`:
`helmet`, `no_helmet`, `person`. Параметры подготовки находятся в `params.yaml`.

Источник и лицензия:
[Construction-PPE](https://docs.ultralytics.com/datasets/detect/construction-ppe/), AGPL-3.0.
