"""Script to generate Airflow DAGs from YAML configuration files."""

import os
import glob
import json
import yaml
from jinja2 import Environment, FileSystemLoader

# Load Jinja template
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("scripts/dag_generator/templates/workflow.yml.j2")

# Loop over environments
for environment in ["development"]:
    print("=" * 100)
    print(f"Processing environment: {environment}")

    for root, dirs, files in os.walk(f"environments/{environment}"):
        for file in glob.glob(os.path.join(root, "configuration.yml")):
            print("=" * 100)
            print(f"Processing configuration: {file}")
            folder = os.path.dirname(file)
            print(f"Folder: {folder}")

            environment = folder.split("/")[1]
            print(f"Environment: {environment}")

            project = folder.split("/")[2]
            print(f"Project: {project}")

            workflow = folder.split("/")[3]
            print(f"Workflow: {workflow}")

            # Load YAML file
            with open(file, "r", encoding="utf-8") as yaml_file:
                config = yaml.safe_load(yaml_file)

            # Update config with environment, project, and workflow
            config.update(
                {
                    "meta": {
                        "environment": environment,
                        "project": project,
                        "workflow": workflow
                    }
                }
            )

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
            output_dir = f"dist/dags/{environment}/{project}/{workflow}"
            os.makedirs(output_dir, exist_ok=True)

            # Write the rendered DAG to a file
            with open(
                f"dist/dags/{environment}/{project}/{workflow}/workflow.yml",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(rendered_dag)
