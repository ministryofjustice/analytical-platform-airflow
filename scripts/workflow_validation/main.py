"""Script to validate generated workflow can be loaded by dagfactory."""
import sys
from pathlib import Path

from dagfactory import load_yaml_dags

workflow_file = sys.argv[1]
print(f"Processing workflow file: {workflow_file}")

file_path = Path(workflow_file).resolve()

dag_bag = {}
load_yaml_dags(
    globals_dict=dag_bag,
    config_filepath=file_path
)

for dag_id, dag in dag_bag.items():
    dag.validate()
    print(f"DAG validated successfully: {dag_id}")
