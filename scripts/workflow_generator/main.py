"""Script to generate Airflow workflow from YAML configuration files."""
import json
import os
import sys

import yaml
from jinja2 import Environment, FileSystemLoader

# Custom filter to merge dictionaries
def merge_dicts(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result


# Load Jinja template
env = Environment(loader=FileSystemLoader("."))
env.filters['merge_dicts'] = merge_dicts
template = env.get_template("scripts/workflow_generator/templates/workflow.yml.j2")

workflow_file = sys.argv[1]
print(f"Processing workflow file: {workflow_file}")

folder = os.path.dirname(workflow_file)
print(f"Folder: {folder}")

environment = folder.split("/")[1]
print(f"Environment: {environment}")

project = folder.split("/")[2]
print(f"Project: {project}")

workflow = folder.split("/")[3]
print(f"Workflow: {workflow}")

# Load YAML file
with open(workflow_file, "r", encoding="utf-8") as yaml_file:
    config = yaml.safe_load(yaml_file)

if config.get("dag", {}).get("python_config", False):
    print("Python config is enabled")
    SOURCE_DIR = f"environments/{environment}/{project}/{workflow}"
    OUTPUT_DIR = f"dist/dags/{environment}/{project}/{workflow}"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Set placeholder replacement value
    repository_name = config["dag"]["repository"]
    repository_tag = config["dag"]["tag"]
    owner = config["tags"]["owner"]

    # Replace placeholders in the dag.py file
    print("Replacing placeholders")
    with open(f"{SOURCE_DIR}/dag.py", "r", encoding="utf-8") as file:
        dag_content = file.read()
        dag_content = dag_content.replace("PLACEHOLDER_REPOSITORY_NAME", repository_name)
        dag_content = dag_content.replace("PLACEHOLDER_REPOSITORY_TAG", repository_tag)
        dag_content = dag_content.replace("PLACEHOLDER_PROJECT", project)
        dag_content = dag_content.replace("PLACEHOLDER_WORKFLOW", workflow)
        dag_content = dag_content.replace("PLACEHOLDER_ENVIRONMENT", environment)
        dag_content = dag_content.replace("PLACEHOLDER_OWNER", owner)

    print("=" * 42 + " Rendered DAG " + "=" * 44)
    print(dag_content)
    print("=" * 100)

    # Write the modified content back to the dag.py file
    with open(f"{OUTPUT_DIR}/dag.py", "w", encoding="utf-8") as file:
        file.write(dag_content)

else:
    print("Python config is disabled")
    # Update config with environment, project, and workflow
    config.update(
        {
            "meta": {
                "environment": environment,
                "project": project,
                "workflow": workflow,
            }
        }
    )

    # Sanitise repository so it matches what is created in ECR
    sanitised_repository = config["dag"]["repository"].lower().replace("_", "-")
    print(f"Sanitised repository: {sanitised_repository}")
    config["dag"]["repository"] = sanitised_repository

    # Modify secrets list to dictionary
    # secrets list looks like ["username", "password"]
    # secrets dictionary needs to look like ["secret":f"{project}-{workflow}-{secret}","deploy_type":"env","deploy_target":"f"SECRET_{secret.upper().replace('-', '_')}", "key": "data"}]
    if config.get("secrets"):
        secrets = config["secrets"]
        secrets_list = []
        for secret in secrets:
            secret_object = {
                "deploy_type": "env",
                "deploy_target": f"SECRET_{secret.upper().replace('-', '_')}",
                "secret": f"{project}-{workflow}-{secret}",
                "key": "data",
            }
            secrets_list.append(secret_object)
        config["secrets"] = secrets_list

    # Print config
    pretty_config = json.dumps(config, indent=4)
    print("=" * 42 + " Configuration " + "=" * 43)
    print(pretty_config)
    print("=" * 100)

    # Render DAG
    print("=" * 42 + " Rendered DAG " + "=" * 44)
    rendered_dag = template.render(config)
    print(rendered_dag)
    print("=" * 100)

    # Ensure the directory exists
    OUTPUT_DIR = f"dist/dags/{environment}/{project}/{workflow}"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Write the rendered DAG to a file
    with open(
        f"dist/dags/{environment}/{project}/{workflow}/workflow.yml",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(rendered_dag)
