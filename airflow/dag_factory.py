from dagfactory import load_yaml_dags

from airflow import DAG

load_yaml_dags(globals_dict=globals(), suffix=["workflow.yml"])
