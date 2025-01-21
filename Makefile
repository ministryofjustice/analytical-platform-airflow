.PHONY: schema_validation dags workflow_validation

schema_validation:
	python scripts/workflow_schema_validation/main.py

dags:
	python scripts/workflow_generator/main.py

workflow_validation: schema_validation dags
	PYTHONPATH=airflow python scripts/workflow_validation/main.py
