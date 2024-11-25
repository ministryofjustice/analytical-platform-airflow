"""Script to generate Airflow DAGs from YAML configuration files."""

import os
import glob
import json
import yaml
from jinja2 import Environment, FileSystemLoader


# Load Jinja template
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("bin/src/dag.py.j2")

# Loop over environments
for environment in ["development"]:
    print(f"Processing environment: {environment}")

    for root, dirs, files in os.walk(f"environments/{environment}"):
        for file in glob.glob(os.path.join(root, "configuration.yaml")):
            print(f"\tProcessing configuration: {file}")
            folder = os.path.dirname(file)
            print(f"\t\tFolder: {folder}")

            environment = folder.split("/")[1]
            print(f"\t\tEnvironment: {environment}")

            project = folder.split("/")[2]
            print(f"\t\tProject: {project}")

            workflow = folder.split("/")[3]
            print(f"\t\tWorkflow: {workflow}")

            # Load YAML file
            with open(file, "r", encoding="utf-8") as yaml_file:
                config = yaml.safe_load(yaml_file)

            # Update config with environment, project, and workflow
            config.update(
                {"environment": environment, "project": project, "workflow": workflow}
            )

            # Print config
            pretty_config = json.dumps(config, indent=4)
            print("Config " + "=" * 80)
            print(pretty_config)
            print("=" * 80)

            # Get compute profile
            # compute_profile = get_compute_profile(
            #     compute_profile=config["compute_profile"]
            # )
            # print("Compute profile " + "=" * 80)
            # print(compute_profile)

            # Merge compute profile into config
            # config.update(compute_profile)
            # print("Merged config " + "=" * 80)
            # print(config)

            # Render template
            print("DAG " + "=" * 80)
            rendered_dag = template.render(config)
            print(rendered_dag)
            print("=" * 80)

            # Ensure the directory exists
            output_dir = f"dist/dags/{environment}/{project}/{workflow}"
            os.makedirs(output_dir, exist_ok=True)

            # Write the rendered DAG to a file
            with open(
                f"dist/dags/{environment}/{project}/{workflow}/dag.py",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(rendered_dag)
