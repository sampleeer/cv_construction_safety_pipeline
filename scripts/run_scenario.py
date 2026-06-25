from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests


def wait_for_service(base_url: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = requests.get(f"{base_url}/health", timeout=3)
            if response.status_code == 200:
                return
        except requests.RequestException as error:
            last_error = error
        time.sleep(2)
    raise RuntimeError(f"Service did not become healthy in {timeout}s: {last_error}")


def assert_json_subset(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        if actual.get(key) != value:
            raise AssertionError(f"Expected JSON field {key}={value!r}, got {actual.get(key)!r}")


def run_check(base_url: str, check: dict[str, Any]) -> dict[str, Any]:
    method = check["method"].upper()
    url = f"{base_url}{check['path']}"
    response = requests.request(method, url, json=check.get("json"), timeout=10)

    expected_status = check.get("expect_status", 200)
    if response.status_code != expected_status:
        raise AssertionError(
            f"{check['name']} failed: expected status {expected_status}, "
            f"got {response.status_code}: {response.text}"
        )

    payload = response.json()
    if "expect_json" in check:
        assert_json_subset(payload, check["expect_json"])
    for key in check.get("expect_keys", []):
        if key not in payload:
            raise AssertionError(f"{check['name']} failed: response lacks key {key}")

    return {"name": check["name"], "status": "passed", "response": payload}


def run_scenario(base_url: str, scenario_path: Path, output_path: Path) -> dict[str, Any]:
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    wait_for_service(base_url)
    results = [run_check(base_url, check) for check in scenario["checks"]]
    report = {
        "scenario": scenario["name"],
        "base_url": base_url,
        "passed": True,
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run functional API scenario.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--scenario", default="scenario.json")
    parser.add_argument("--output", default="reports/functional_test_results.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        report = run_scenario(args.base_url, Path(args.scenario), Path(args.output))
    except Exception as error:
        print(f"Scenario failed: {error}", file=sys.stderr)
        raise
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
