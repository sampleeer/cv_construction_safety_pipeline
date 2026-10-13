import json
from pathlib import Path

import numpy as np
import onnx
import pytest
from onnx import TensorProto, helper, numpy_helper

from src.cv.detector import sha256


@pytest.fixture
def manifest(tmp_path: Path) -> Path:
    # A real ONNX graph with overlapping boxes and two classes.
    output = np.array([[[16, 17, 16], [16, 16, 16], [16, 16, 16], [16, 16, 16],
                        [.9, .8, .1], [.1, .1, .85]]], dtype=np.float32)
    graph = helper.make_graph(
        [helper.make_node('Constant', [], ['output'], value=numpy_helper.from_array(output))],
        'fixture', [helper.make_tensor_value_info('images', TensorProto.FLOAT, [1, 3, 32, 32])],
        [helper.make_tensor_value_info('output', TensorProto.FLOAT, [1, 6, 3])],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 17)])
    model.ir_version = 9
    artifact = tmp_path / 'detector.onnx'
    onnx.save(model, artifact)
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps({'artifact': artifact.name, 'sha256': sha256(artifact),
                                'version': 'test-fixture', 'labels': ['person', 'car'], 'input_size': 32}))
    return path
