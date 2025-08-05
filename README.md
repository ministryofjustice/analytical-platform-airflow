# Analytical Platform Airflow

[![Ministry of Justice Repository Compliance Badge](https://github-community.service.justice.gov.uk/repository-standards/api/analytical-platform-airflow/badge)](https://github-community.service.justice.gov.uk/repository-standards/analytical-platform-airflow)

[![Open in Dev Container](https://raw.githubusercontent.com/ministryofjustice/.devcontainer/refs/heads/main/contrib/badge.svg)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/ministryofjustice/analytical-platform-airflow)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ministryofjustice/analytical-platform-airflow)

Please refer to our [User Guidance](https://user-guidance.analytical-platform.service.justice.gov.uk/services/airflow) for information on how to use Analytical Platform Airflow.

Commit signature verification is enabled on this repository. To set this up follow the instructions [on GitHub](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#ssh-commit-signature-verification).


## 🧪 Running Workflow Scripts Locally

This project contains utility scripts under the `scripts/` directory that support DAG development and validation.

These scripts import internal modules from the `airflow/analytical_platform` package. To ensure Python can resolve these imports, you must set the `PYTHONPATH` environment variable when running the scripts locally.


### ✅ Quick Start

1. Install project dependencies using [`uv`](https://github.com/astral-sh/uv):

    ```bash
    uv venv
    uv pip install -r requirements.txt
    ```

2. Run a script using PYTHONPATH=airflow:

    ```bash
    # to validate the source workflow schema
    PYTHONPATH=airflow uv run python scripts/workflow_schema_validation/main.py path/to/source/workflow.yml

    # to build the dist workflow.yml
    PYTHONPATH=airflow uv run python scripts/workflow_generator/main.py path/to/source/workflow.yml

    # to validate the dist workflow.yml
    PYTHONPATH=airflow uv run python scripts/workflow_validation/main.py path/to/dist/workflow.yml
    ```

### 📚 Why PYTHONPATH Is Needed

The internal code is located under the airflow/ directory. Scripts use imports like:

    ```python
    from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
    ```

Without setting PYTHONPATH=airflow, Python will not recognise analytical_platform as a valid module, since it's nested under the airflow/ directory.


### 🤖 Dev Containers and CI/CD

In development containers and GitHub Actions workflows, PYTHONPATH=airflow is already set.

You only need to configure this manually when running scripts directly on your local machine.
