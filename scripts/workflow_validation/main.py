"""Script to validate generated workflow can be loaded by dagfactory."""
import sys
from pathlib import Path

from dagfactory import load_yaml_dags

workflow_file = sys.argv[1]
print(f"Processing workflow file: {workflow_file}")

file_path = Path(workflow_file).resolve()

load_yaml_dags(
    globals_dict=globals(),
    config_filepath=file_path
)

# if we got this far without an exception the DAG is valid
print(f"DAG loaded successfully: {file_path}")
