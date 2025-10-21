# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the Analytical Platform Airflow repository for the Ministry of Justice, used to configure and manage data workflow jobs in AWS MWAA (Managed Workflows for Apache Airflow). The repository supports two distinct approaches for defining DAGs:

1. **YAML-based workflows** using DAG Factory (declarative configuration)
2. **Python-based DAGs** using direct Airflow DAG definitions

## Common Development Commands

### Environment Setup
```bash
# Install dependencies (uses UV package manager)
uv venv
uv pip install --requirements requirements.txt

# Initialize git submodules (required for MWAA local runner)
git submodule init && git submodule update
```

### Workflow Development
```bash
# Validate workflow YAML schema
PYTHONPATH="airflow" uv run python scripts/workflow_schema_validation/main.py path/to/source/workflow.yml

# Generate workflow.yml files
PYTHONPATH="airflow" uv run python scripts/workflow_generator/main.py path/to/source/workflow.yml

# Validate generated workflows
PYTHONPATH="airflow" uv run python scripts/workflow_validation/main.py path/to/dist/workflow.yml
```

### Make Targets
```bash
make clean                # Remove dist directory
make schema_validation    # Validate all workflow schemas
make dags                 # Generate DAGs from workflows (includes schema validation and clean)
make workflow_validation  # Full validation pipeline
```

### Code Quality
- **Linting**: flake8 (max line length: 120)
- **Formatting**: black, autopep8, isort
- **Type checking**: mypy
- **Python version**: 3.11

## Architecture Overview

### Directory Structure
- `airflow/`: Core Airflow code and custom operators
  - `analytical_platform/`: Custom operators and utilities
    - `standard_operator.py`: Main KubernetesPodOperator wrapper
    - `compute_profiles.py`: Kubernetes resource configurations
  - `dag_factory.py`: DAG Factory integration for YAML workflows
- `environments/`: Environment-specific workflow configurations
- `scripts/`: Development utilities for validation and generation
- `terraform/`: Infrastructure as Code

### Two DAG Approaches

#### 1. YAML-based Workflows (DAG Factory)
Located in `environments/{env}/{project}/{workflow}/workflow.yml`

**Key features:**
- Declarative configuration
- Built-in Slack notifications via `slack_channel` field
- Automatic DAG generation via DAG Factory
- Schema validation

**Example structure:**
```yaml
dag:
  repository: org/repo-name
  tag: v1.0.0
  compute_profile: general-spot-1vcpu-4gb

notifications:
  emails:
    - user@justice.gov.uk
  slack_channel: my-notifications-channel

iam:
  external_role: arn:aws:iam::123456789:role/my-role
```

#### 2. Python DAGs
Located in `environments/{env}/{project}/{workflow}/dag.py`

**Key features:**
- Direct Airflow DAG definitions
- Uses `AnalyticalPlatformStandardOperator`
- Email notifications via `default_args`
- More programmatic control

**For Slack notifications in Python DAGs:**
Currently, Python DAGs use email notifications through `default_args`. To add Slack notifications similar to YAML workflows, you would need to:
1. Import Slack operators from `airflow.providers.slack`
2. Add Slack webhook configuration
3. Implement failure/success callbacks using Slack operators

### AnalyticalPlatformStandardOperator

This is a wrapper around `KubernetesPodOperator` that provides:
- Standardized compute profiles
- Security context configurations
- Custom XCom sidecar container
- Environment variable injection
- Secret management integration

**Required parameters:**
- `compute_profile`: One of the predefined profiles (see `compute_profiles.py`)
- `image`: Container image URL
- `environment`, `project`, `workflow`: Naming convention fields

### PYTHONPATH Requirement

**Critical**: When running scripts locally, always set `PYTHONPATH="airflow"` to ensure Python can resolve imports from the `analytical_platform` module.

## Development Workflow

1. **For YAML workflows:**
   - Edit `workflow.yml` in appropriate environment directory
   - Run schema validation
   - Generate DAGs
   - Validate generated workflows

2. **For Python DAGs:**
   - Edit `dag.py` directly
   - Ensure proper imports from `analytical_platform`
   - Test locally with proper PYTHONPATH

3. **Local Airflow testing** (Engineering team only):
   - Initialize submodules
   - Build MWAA Local Runner: `./mwaa-local-env build-image`
   - Connect to Analytical Platform Compute
   - Start local runner: `./mwaa-local-env start`
   - Access at http://localhost:8080 (admin/test)

## Key Conventions

- Python version: 3.11
- DAG naming: `{PROJECT}.{WORKFLOW}`
- Image naming: `509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}`
- Environment variables use uppercase with underscores
- All workflows require proper IAM role configuration