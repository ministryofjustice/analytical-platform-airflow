"""Script to validate Airflow DAG configuration files against a JSON schema."""

import glob
import json
import os
import sys

import yaml
from cerberus import Validator

# Load JSON schema
with open(
    "scripts/workflow_schema_validation/schema.json", "r", encoding="utf-8"
) as schema_file:
    schema = json.load(schema_file)

# Loop over environments
for environment in ["development", "test",  "production"]:
    print("=" * 100)
    print(f"Processing environment: {environment}")

    for root, dirs, files in os.walk(f"environments/{environment}"):
        for file in glob.glob(os.path.join(root, "workflow.yml")):
            # Load YAML file
            with open(file, "r", encoding="utf-8") as yaml_file:
                yaml_document = yaml_file.read()

            v = Validator(schema)

            # Validate the document
            if v.validate(yaml.safe_load(yaml_document)):
                print(f"Configuration {file} is valid")
            else:
                print(f"Configuration {file} is invalid")
                print(json.dumps(v.errors, indent=4))
                sys.exit(1)
