.PHONY: dags

dags:
	python scripts/workflow_generator/main.py

schema_validation:
	python scripts/workflow_schema_validation/main.py
