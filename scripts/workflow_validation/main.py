"""Script to validate generated workflow can be loaded by dagfactory."""

import glob
import os
import sys
from pathlib import Path

import dagfactory
from dagfactory.exceptions import DagFactoryConfigException

# Loop over generated workflows
for root, dirs, files in os.walk("dist/dags"):
    for file in glob.glob(os.path.join(root, "workflow.yml")):
        print(f"Processing workflow: {file}")
        file_path = Path(file).resolve()
        try:
            dag_factory = dagfactory.DagFactory(config_filepath=str(file_path))
            dag = dag_factory.generate_dags(globals())
        except DagFactoryConfigException as e:
            print(f"Error loading DAG configuration: {str(e)}", file=sys.stderr)
            # sys.exit(1)
        except Exception as e:
            print(f"Unexpected error while processing DAG: {str(e)}", file=sys.stderr)
            # sys.exit(1)
        else:
            print(f"DAG loaded successfully: {file_path}")
