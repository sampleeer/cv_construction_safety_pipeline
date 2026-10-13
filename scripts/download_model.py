"""Fetch official pretrained YOLO11n weights (run only in the export environment)."""
from pathlib import Path
import shutil

from ultralytics import YOLO

path = Path('models/source/yolo11n.pt')
path.parent.mkdir(parents=True, exist_ok=True)
if not path.exists():
    model = YOLO('yolo11n.pt')
    shutil.move(str(model.ckpt_path), path)
print(path)
