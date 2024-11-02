"""Script to generate Airflow DAGs from YAML configuration files."""

import os
import glob
import json
import yaml
from jinja2 import Environment, FileSystemLoader
from utils.compute_profiles import get_compute_profile

# Load Jinja template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('src/templates/dag.jinja2')

# Loop over environments
for environment in ['development']:
    print(f'Processing environment: {environment}')

    for root, dirs, files in os.walk(f'configuration/environments/{environment}'):

        for file in glob.glob(os.path.join(root, 'dag.yaml')):
            print(f'\tProcessing DAG manifest: {file}')
            folder = os.path.dirname(file)

            # Load YAML file
            with open(file, 'r', encoding='utf-8') as yaml_file:
                config = yaml.safe_load(yaml_file)

            # Print config
            pretty_config = json.dumps(config, indent=4)
            print('Config ' + '=' * 80)
            print(pretty_config)
            print('=' * 80)

            # Get compute profile
            compute_profile = get_compute_profile(compute_profile=config['compute_profile'])
            print('Compute profile ' + '=' * 80)
            print(compute_profile)

            # Merge compute profile into config
            config.update(compute_profile)
            print('Merged config ' + '=' * 80)
            print(config)

            # Render template
            print('DAG ' + '=' * 80)
            rendered_dag = template.render(config)
            print(rendered_dag)
            print('=' * 80)

            # Write the rendered DAG to a file
            with open(f'{folder}/dag.py', 'w', encoding='utf-8') as f:
                f.write(rendered_dag)
