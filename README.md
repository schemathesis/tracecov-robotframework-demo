# TraceCov + Robot Framework demo

Robot Framework suites test [Swagger Petstore](https://github.com/swagger-api/swagger-petstore), and TraceCov measures API coverage per suite and test. `just ship` sends the results to Elasticsearch for Kibana.

## Requirements

- Docker, [uv](https://docs.astral.sh/uv/) and [just](https://just.systems); free ports 8080, 9200 and 5601.
- The TraceCov Professional wheel in `wheels/`. The Community edition writes only the overall report.

## Run

```console
$ just up          # Petstore, Elasticsearch, Kibana
$ just test        # run the suites; output goes to results/
$ just test-pabot  # the same under pabot
$ just queries     # answer three questions from results/
$ just ship        # send the run to Elasticsearch
$ just kibana      # load the dashboard: http://localhost:5601/app/dashboards#/view/tracecov
$ just history     # three runs (smoke, regression, all) for the trend chart
$ just down        # stop and delete all data
```

Expect failures: two tests hit real Petstore bugs, and most generated tests fail on its 500s. TraceCov counts their requests anyway.

## Add it to your suite

```console
$ pip install --find-links wheels tracecov-professional==0.26.0
$ robot --listener "tracecov.robotframework.TraceCov;openapi.json;data=tracecov.data" tests
```

The listener records requests sent through `requests` (RequestsLibrary, SchemathesisLibrary) and labels them with the test and suite. It writes `tracecov-report.html` next to `report.html` and links it there as **API Coverage**. `data=` saves the raw data for scripts like `queries.py` and `ship.py`. More in the [Robot Framework guide](https://docs.tracecov.sh/integration/robotframework/).

## Elasticsearch

`ship.py` is example code, not part of TraceCov. It writes four document kinds to the `tracecov` index: `run`, `label` (a test or suite), `element` (what one test reached) and `failing_only`.

```text
kind:element and path:"/pet" and method:POST   tests that reached POST /pet
kind:failing_only                              reached only by failing tests
kind:label and label_kind:suite                coverage per suite
```
