from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    "dist",
}

EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_FILES = {".coverage"}


def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    if path.parts[:2] in {(".dvc", "cache"), (".dvc", "tmp")}:
        return False
    if path.name in EXCLUDE_FILES:
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def create_zip(output_path: Path, root: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file() and should_include(path.relative_to(root)):
                archive.write(path, path.relative_to(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create model distribution zip.")
    parser.add_argument("--output", default="dist/celeba_smiling_mlops.zip")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    create_zip(output_path=output_path, root=Path.cwd())
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
