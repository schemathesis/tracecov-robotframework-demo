"""Generate dashboard.ndjson: run `python kibana/build.py > kibana/dashboard.ndjson`."""

import json

INDEX = {"name": "kibanaSavedObjectMeta.searchSourceJSON.index", "type": "index-pattern", "id": "tracecov"}


def terms(id: str, field: str, schema: str, size: int, label: str, order: str = "desc", order_by: str = "1") -> dict:
    return {
        "id": id,
        "enabled": True,
        "type": "terms",
        "schema": schema,
        "params": {"field": field, "size": size, "order": order, "orderBy": order_by, "customLabel": label},
    }


def metric(id: str, kind: str, label: str, field: str | None = None) -> dict:
    params = {"customLabel": label}
    if field:
        params["field"] = field
    return {"id": id, "enabled": True, "type": kind, "schema": "metric", "params": params}


def table(id: str, title: str, query: str, aggs: list[dict]) -> dict:
    state = {
        "title": title,
        "type": "table",
        "aggs": aggs,
        "params": {
            "perPage": 20,
            "showPartialRows": False,
            "showMetricsAtAllLevels": False,
            "showTotal": False,
            "totalFunc": "sum",
            "percentageCol": "",
        },
    }
    return visualization(id, title, state, query)


def line(id: str, title: str, query: str, metrics: list[dict], x: dict) -> dict:
    series = [
        {
            "show": True,
            "type": "line",
            "mode": "normal",
            "data": {"id": m["id"], "label": m["params"]["customLabel"]},
            "valueAxis": "ValueAxis-1",
            "drawLinesBetweenPoints": True,
            "showCircles": True,
            "lineWidth": 2,
        }
        for m in metrics
    ]
    params = {
        "type": "line",
        "addTooltip": True,
        "addLegend": True,
        "legendPosition": "right",
        "times": [],
        "addTimeMarker": False,
        "grid": {"categoryLines": False},
        "categoryAxes": [
            {
                "id": "CategoryAxis-1",
                "type": "category",
                "position": "bottom",
                "show": True,
                "scale": {"type": "linear"},
                "labels": {"show": True, "filter": False, "truncate": 100},
                "title": {},
            }
        ],
        "valueAxes": [
            {
                "id": "ValueAxis-1",
                "name": "LeftAxis-1",
                "type": "value",
                "position": "left",
                "show": True,
                "scale": {"type": "linear", "mode": "normal", "setYExtents": True, "min": 0, "max": 100},
                "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                "title": {"text": "%"},
            }
        ],
        "seriesParams": series,
    }
    state = {"title": title, "type": "line", "aggs": [*metrics, x], "params": params}
    return visualization(id, title, state, query)


def visualization(id: str, title: str, state: dict, query: str) -> dict:
    search = {"query": {"query": query, "language": "kuery"}, "filter": [], "indexRefName": INDEX["name"]}
    return {
        "type": "visualization",
        "id": id,
        "attributes": {
            "title": title,
            "visState": json.dumps(state),
            "uiStateJSON": "{}",
            "description": "",
            "version": 1,
            "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search)},
        },
        "references": [INDEX],
    }


panels = [
    line(
        "tracecov-trend",
        "Coverage per run",
        "kind:run",
        [
            metric("1", "max", "Operations %", "operations.percent"),
            metric("2", "max", "Parameters %", "parameters.percent"),
            metric("3", "max", "Keywords %", "keywords.percent"),
            metric("4", "max", "Responses %", "responses.percent"),
        ],
        terms("5", "run.keyword", "segment", 50, "Run", order="asc", order_by="_key"),
    ),
    table(
        "tracecov-suites",
        "Coverage per suite",
        "kind:label and label_kind:suite",
        [
            metric("1", "max", "Operations %", "operations.percent"),
            metric("2", "max", "Keywords %", "keywords.percent"),
            terms("3", "run.keyword", "bucket", 50, "Run", order_by="_key"),
            terms("4", "label.keyword", "bucket", 50, "Suite", order="asc", order_by="_key"),
        ],
    ),
    table(
        "tracecov-failing-only",
        "Reached only by failing tests",
        "kind:failing_only",
        [
            metric("1", "count", "Runs"),
            terms("2", "element.keyword", "bucket", 200, "Element"),
            terms("3", "reached.keyword", "bucket", 3, "Values sent"),
        ],
    ),
    table(
        "tracecov-tests-per-element",
        "Tests per element",
        "kind:element",
        [
            metric("1", "cardinality", "Tests", "label.keyword"),
            terms("2", "element.keyword", "bucket", 500, "Element"),
            terms("3", "status.keyword", "bucket", 3, "Test status"),
        ],
    ),
    table(
        "tracecov-elements-per-test",
        "Elements per test",
        "kind:element",
        [
            metric("1", "cardinality", "Elements", "element.keyword"),
            terms("2", "group.keyword", "bucket", 200, "Test (generated tests by operation)"),
            terms("3", "status.keyword", "bucket", 3, "Status"),
        ],
    ),
]

layout = [(0, 0, 48, 14), (0, 14, 24, 16), (24, 14, 24, 16), (0, 30, 24, 20), (24, 30, 24, 20)]
dashboard_panels = []
references = []
for number, (panel, (x, y, w, h)) in enumerate(zip(panels, layout), start=1):
    ref = f"panel_{number}"
    dashboard_panels.append(
        {
            "panelIndex": str(number),
            "gridData": {"x": x, "y": y, "w": w, "h": h, "i": str(number)},
            "embeddableConfig": {},
            "panelRefName": ref,
            "version": "8.15.3",
        }
    )
    references.append({"name": ref, "type": "visualization", "id": panel["id"]})

dashboard = {
    "type": "dashboard",
    "id": "tracecov",
    "attributes": {
        "title": "TraceCov",
        "description": "API coverage per run, suite, test and element",
        "panelsJSON": json.dumps(dashboard_panels),
        "optionsJSON": json.dumps({"useMargins": True}),
        "timeRestore": True,
        "timeFrom": "now-7d",
        "timeTo": "now",
        "version": 1,
        "kibanaSavedObjectMeta": {
            "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
        },
    },
    "references": references,
}

data_view = {
    "type": "index-pattern",
    "id": "tracecov",
    "attributes": {"title": "tracecov", "name": "TraceCov", "timeFieldName": "generated_at"},
    "references": [],
}

for item in [data_view, *panels, dashboard]:
    print(json.dumps(item))
