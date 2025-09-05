# Analytical Platform Airflow

[![Ministry of Justice Repository Compliance Badge](https://github-community.service.justice.gov.uk/repository-standards/api/analytical-platform-airflow/badge)](https://github-community.service.justice.gov.uk/repository-standards/analytical-platform-airflow)

[![Open in Dev Container](https://raw.githubusercontent.com/ministryofjustice/.devcontainer/refs/heads/main/contrib/badge.svg)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/ministryofjustice/analytical-platform-airflow)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ministryofjustice/analytical-platform-airflow)

Please refer to our [User Guidance](https://user-guidance.analytical-platform.service.justice.gov.uk/services/airflow) for information on how to use Analytical Platform Airflow.

Commit signature verification is enabled on this repository. To set this up follow the instructions [on GitHub](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#ssh-commit-signature-verification).

## 🧪 Running Workflow Scripts Locally

This project contains utility scripts under the [`scripts`](./scripts/) directory that support DAG development and validation.

These scripts import internal modules from the [`airflow/analytical_platform`](./airflow/analytical_platform/) package. To ensure Python can resolve these imports, you must set the `PYTHONPATH` environment variable when running the scripts locally.

### ✅ Quick Start

> [!NOTE]
> If you use the provided development container, it automatically handles package installation and setting `PYTHONPATH`

1. Install project dependencies using [`uv`](https://github.com/astral-sh/uv):

   ```bash
   uv venv

   uv pip install --requirements requirements.txt
   ```

2. Run scripts:

   ```bash
   # to validate the source workflow schema
   PYTHONPATH="airflow" uv run python scripts/workflow_schema_validation/main.py path/to/source/workflow.yml

   # to build the dist workflow.yml
   PYTHONPATH="airflow" uv run python scripts/workflow_generator/main.py path/to/source/workflow.yml

   # to validate the dist workflow.yml
   PYTHONPATH="airflow" uv run python scripts/workflow_validation/main.py path/to/dist/workflow.yml
   ```

### 📚 Why `PYTHONPATH` is Needed

The internal code is located under the [`airflow`](./airflow/) directory. Scripts use import statements like:

```python
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
```

Without setting `PYTHONPATH=airflow`, Python will not recognise [`analytical_platform`](./airflow/analytical_platform/) as a valid module, since it's nested under the [`airflow`](./airflow/) directory.

## ⚗️ Running Airflow Locally

> [!IMPORTANT]
> This is only available to Analytical Platform's [engineering team](https://github.com/orgs/ministryofjustice/teams/analytical-platform-engineers)

1. Initialise submodules

   ```bash
   git submodule init

   git submodule update
   ```

1. Change into MWAA Local Runner directory

   ```bash
   cd aws-mwaa-local-runner
   ```

1. Build MWAA Local Runner

   > [!NOTE]
   > Depending on your internet speed, this may take a while

   ```bash
   ./mwaa-local-env build-image
   ```

1. Connect to Analytical Platform Compute

   ```bash
   aws-sso login

   aws-sso exec --profile "analytical-platform-compute-${ENVIRONMENT:-"development"}:platform-engineer-admin"

   aws eks update-kubeconfig --name "${AWS_SSO_PROFILE%%:*}"
   ```

1. Start MWAA Local Runner

   ```bash
   ./mwaa-local-env start
   ```

1. Log in to Airflow <http://localhost:8080>

- Username: admin
- Password: test

[!NOTE]
To test a workflow locally, edit one of the exsting example DAGs, as these already have the necessary serviceaccount and IAM role.
If a new workflow is created and tested locally, the task will fail due to the serviceaccount and IAM role being missing.
