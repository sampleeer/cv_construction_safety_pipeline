from __future__ import annotations

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml


def run_command(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def last_commit_hashes(limit: int = 5) -> list[str]:
    output = run_command(["git", "log", f"-{limit}", "--pretty=format:%H"])
    return output.splitlines() if output else []


def docker_image_id(image: str) -> str | None:
    return run_command(["docker", "image", "inspect", image, "--format", "{{.Id}}"])


def coverage_percent(path: Path) -> float | None:
    if not path.exists():
        return None
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    line_rate = root.attrib.get("line-rate")
    if line_rate is None:
        return None
    return round(float(line_rate) * 100, 2)


def build_report(image: str, coverage_path: Path) -> dict[str, Any]:
    image_id = docker_image_id(image)
    return {
        "docker_image": {
            "name": image,
            "image_id": image_id,
            "sha256": image_id.removeprefix("sha256:") if image_id else None,
        },
        "git": {
            "last_5_commits": last_commit_hashes(5),
        },
        "tests": {
            "coverage_percent": coverage_percent(coverage_path),
            "coverage_source": str(coverage_path),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate dev_sec_ops.yml metadata.")
    parser.add_argument("--image", default="celeba-smiling-api:local")
    parser.add_argument("--coverage", default="coverage.xml")
    parser.add_argument("--output", default="dev_sec_ops.yml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.image, Path(args.coverage))
    output_path = Path(args.output)
    output_path.write_text(
        yaml.safe_dump(report, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
