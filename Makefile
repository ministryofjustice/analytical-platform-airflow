.PHONY: clean schema_validation dags workflow_validation test precommit-install precommit-run

WORKERS ?= auto

clean:
	rm --force --recursive dist

schema_validation:
	python scripts/workflow_schema_validation/main.py

dags: schema_validation clean
	python scripts/workflow_generator/main.py

workflow_validation: schema_validation dags
	PYTHONPATH=airflow python scripts/workflow_validation/main.py

test: clean
	PYTHONPATH=airflow uv run pytest tests/ -v -x -n $(WORKERS) $(ARGS)

precommit-install:
	uvx pre-commit install --install-hooks

precommit-run:
	uvx pre-commit run --all-files
