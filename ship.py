"""Send one Robot Framework run's coverage to Elasticsearch.

Reads `results/output.xml` (test status and tags), `results/tracecov-report.json` (totals) and
`results/tracecov.data` (which elements each test reached), and writes four kinds of documents
into one index:

- `run`: the whole run's coverage totals;
- `label`: one per test and suite, with its totals, status and tags;
- `element`: one per test and element it reached;
- `failing_only`: one per element that only failing tests reached.
"""

import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path

import requests
from robot.api import ExecutionResult
from tracecov import CoverageMap

RESULTS = Path("results")
ELASTIC_URL = os.environ.get("ELASTIC_URL", "http://localhost:9200")
INDEX = "tracecov"
ELEMENT_KEYS = ("method", "path", "location", "name", "response_status", "media_type", "keyword")


def group(test) -> str:
    # SchemathesisLibrary names each generated test `<operation> - <random id>`, a fresh name
    # every run; group them by operation so runs stay comparable.
    if "generated" in test.tags:
        return test.name.rsplit(" - ", 1)[0]
    return test.full_name


def walk(suite):
    yield suite
    for child in suite.suites:
        yield from walk(child)


def documents():
    report = json.loads((RESULTS / "tracecov-report.json").read_text())
    result = ExecutionResult(str(RESULTS / "output.xml"))
    coverage = CoverageMap.from_path("openapi.json")
    coverage.merge_data((RESULTS / "tracecov.data").read_bytes())

    run = {"run": os.environ.get("RUN_ID", report["generated_at"]), "generated_at": report["generated_at"]}
    tests = list(result.suite.all_tests)
    stats = result.statistics.total

    yield {
        **run,
        "kind": "run",
        "passed": stats.passed,
        "failed": stats.failed,
        "skipped": stats.skipped,
        **report["summary"],
    }

    labels = report.get("labels", {})
    for test in tests:
        fields = {
            **run,
            "label": test.full_name,
            "group": group(test),
            "suite": test.parent.full_name,
            "status": test.status,
            "tags": list(test.tags),
        }
        yield {**fields, "kind": "label", "label_kind": "test", **labels.get(test.full_name, {})}
        for row in coverage.label_entries([test.full_name]):
            yield {**fields, "kind": "element", **element(row)}
    for suite in walk(result.suite):
        if suite.full_name in labels:
            yield {
                **run,
                "kind": "label",
                "label": suite.full_name,
                "label_kind": "suite",
                "status": suite.status,
                **labels[suite.full_name],
            }

    failing = [test.full_name for test in tests if test.status == "FAIL"]
    passing = [test.full_name for test in tests if test.status == "PASS"]
    for row in coverage.label_entries(failing, excluding=passing):
        yield {**run, "kind": "failing_only", **element(row)}


def element(row: Mapping) -> dict:
    # `status` in a row is a response status code; keep it apart from the test status.
    doc = {("response_status" if key == "status" else key): value for key, value in row.items()}
    doc["element"] = " ".join(str(doc[key]) for key in ELEMENT_KEYS if key in doc)
    return doc


def create_index() -> None:
    # Without this, Elasticsearch maps a timestamp-like `run` as a date, and it can't be grouped by.
    mappings = {"date_detection": False, "properties": {"generated_at": {"type": "date"}}}
    response = requests.put(f"{ELASTIC_URL}/{INDEX}", json={"mappings": mappings}, timeout=60)
    if response.status_code != 400 or "already_exists" not in response.text:
        response.raise_for_status()


def main() -> None:
    create_index()
    docs = list(documents())
    body = "".join(f'{{"index":{{}}}}\n{json.dumps(doc)}\n' for doc in docs)
    response = requests.post(
        f"{ELASTIC_URL}/{INDEX}/_bulk",
        data=body,
        headers={"Content-Type": "application/x-ndjson"},
        timeout=60,
    )
    response.raise_for_status()
    if response.json()["errors"]:
        sys.exit(f"Elasticsearch rejected some documents: {response.text[:2000]}")
    print(f"Sent {len(docs)} documents to {ELASTIC_URL}/{INDEX}")


if __name__ == "__main__":
    main()
