"""Script to validate workflow configuration files against a JSON schema."""

import json
import sys

import yaml
from cerberus import Validator

# Load JSON schema
with open(
    "scripts/workflow_schema_validation/schema.json", "r", encoding="utf-8"
) as schema_file:
    schema = json.load(schema_file)

workflow_file = sys.argv[1]
print(f"Processing workflow file: {workflow_file}")

# Load YAML file
with open(workflow_file, "r", encoding="utf-8") as yaml_file:
    yaml_document = yaml_file.read()

v = Validator(schema)

# Validate the document
if v.validate(yaml.safe_load(yaml_document)):
    print(f"Configuration {workflow_file} is valid")
    print(json.dumps(v.document, indent=4))
else:
    print(f"Configuration {workflow_file} is invalid")
    print(json.dumps(v.errors, indent=4))
    sys.exit(1)
