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

def validate_textract_s3(config):
    iam_config = config.get("iam", {}) if isinstance(config, dict) else {}
    if not iam_config.get("textract"):
        return {}

    s3_read_only = iam_config.get("s3_read_only")
    if not s3_read_only:
        return {
            "iam": {
                "s3_read_only": ["required when iam.textract is true"]
            }
        }

    return {}

# Validate the document
config = yaml.safe_load(yaml_document)

if v.validate(config):
    extra_errors = validate_textract_s3(config)
    if extra_errors:
        print(f"Configuration {workflow_file} is invalid")
        print(json.dumps(extra_errors, indent=4))
        sys.exit(1)

    print(f"Configuration {workflow_file} is valid")
    print(json.dumps(v.document, indent=4))
else:
    print(f"Configuration {workflow_file} is invalid")
    print(json.dumps(v.errors, indent=4))
    sys.exit(1)
