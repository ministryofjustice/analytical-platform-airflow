"""Script to validate generated workflow can be loaded by dagfactory."""
import sys
from pathlib import Path

import dagfactory


workflow_file = sys.argv[1]
print(f"Processing workflow file: {workflow_file}")

file_path = Path(workflow_file).resolve()

dag_factory = dagfactory.DagFactory(config_filepath=str(file_path))
dag = dag_factory.generate_dags(globals())
# if we got this far without an exception the DAG is valid
print(f"DAG loaded successfully: {file_path}")
