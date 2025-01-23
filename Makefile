.PHONY: clean schema_validation dags workflow_validation

clean:
	rm --force --recursive dist

schema_validation:
	python scripts/workflow_schema_validation/main.py

dags: clean
	python scripts/workflow_generator/main.py

workflow_validation: schema_validation dags
	PYTHONPATH=airflow python scripts/workflow_validation/main.py
