listener := "tracecov.robotframework.TraceCov;openapi.json;data=tracecov.data"

# Start Petstore, Elasticsearch and Kibana
up:
    docker compose up -d --wait

down:
    docker compose down

# Petstore keeps its data in memory; a fresh container makes every run start from the same data
reset:
    docker compose up -d --wait --force-recreate petstore

# Run the suites; pass robot options, e.g. `just test --include smoke`
test *args: reset
    -uv run robot --listener "{{listener}}" --outputdir results {{args}} tests

# The same under pabot, one process per suite
test-pabot *args: reset
    -uv run pabot --listener "{{listener}}" --outputdir results {{args}} tests

# Send the last run to Elasticsearch
ship:
    uv run python ship.py

queries:
    uv run python queries.py

# Three runs with a growing selection of tests, so Kibana has a trend to show
history:
    just test --include smoke && RUN_ID=1-smoke just ship
    just test --include smoke --include regression && RUN_ID=2-regression just ship
    just test && RUN_ID=3-all just ship

# Load the TraceCov data view and dashboard into Kibana
kibana:
    curl -sf -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" -H "kbn-xsrf: true" --form file=@kibana/dashboard.ndjson > /dev/null
    @echo "Open http://localhost:5601/app/dashboards#/view/tracecov"
