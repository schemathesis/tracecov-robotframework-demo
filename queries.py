"""Ask a run's coverage data questions from the terminal, no Elasticsearch needed."""

from collections import Counter
from pathlib import Path

from robot.api import ExecutionResult
from tracecov import CoverageMap

RESULTS = Path("results")

coverage = CoverageMap.from_path("openapi.json")
coverage.merge_data((RESULTS / "tracecov.data").read_bytes())
tests = list(ExecutionResult(str(RESULTS / "output.xml")).suite.all_tests)

print("Which tests reached POST /pet?")
for test in tests:
    if any(row["method"] == "POST" and row["path"] == "/pet" for row in coverage.label_entries([test.full_name])):
        print(f"  {test.status:4}  {test.full_name}")

failing = [test.full_name for test in tests if test.status == "FAIL"]
passing = [test.full_name for test in tests if test.status == "PASS"]
print("\nWhat only failing tests reached:")
for row in coverage.label_entries(failing, excluding=passing):
    print(f"  {row}")

print("\nElements reached per tag:")
for tag in ("smoke", "regression", "generated"):
    labels = [test.full_name for test in tests if tag in test.tags]
    rows = coverage.label_entries(labels)
    print(f"  {tag:10} {len(labels):3} tests  {len(rows):4} elements  {dict(Counter(row['reached'] for row in rows))}")
