"""Download the official Construction-PPE archive into the project, without extraction."""
import urllib.request
from pathlib import Path

from src.helmet.dataset import SOURCE_URL

path = Path('data/raw/ppe/construction-ppe.zip')
path.parent.mkdir(parents=True, exist_ok=True)
if not path.exists():
    temporary = path.with_suffix('.download')
    try:
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as response, temporary.open('wb') as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
print(path)
