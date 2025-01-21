.PHONY: dags schema_validation workflow_validation

dags:
	python scripts/workflow_generator/main.py

schema_validation:
	python scripts/workflow_schema_validation/main.py

workflow_validation: dags
	PYTHONPATH=airflow python scripts/workflow_validation/main.py
