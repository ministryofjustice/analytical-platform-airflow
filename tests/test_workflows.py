#!/usr/bin/env python3
"""
Unit tests for workflows.
Ensures that all workflows can be successfully generated and validated.
These tests will be run in CI whenever a change to the scripts dir are detected, to catch any errors
with the newly generated workflows before they are deployed to Airflow.
"""
import sys
import subprocess
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).parent.parent

# Also defined in scripts/workflow_generator/main.py
PROJECT_ALIASES = {
    "electronic-monitoring-data-store": "emds",
}

ENVIRONMENTS_DIR = WORKSPACE_ROOT / "environments"


def find_all_workflows():
    """Find all workflow files across all environments."""
    return sorted(ENVIRONMENTS_DIR.rglob("workflow.yml"))


def workflow_id(workflow_file):
    """Generate a readable test ID from the workflow file path."""
    relative = workflow_file.relative_to(ENVIRONMENTS_DIR)
    # e.g. "production/hmcts/libra-extract" or "development/analytical-platform/example-schedule"
    return str(relative.parent)


@pytest.mark.parametrize("workflow_file", find_all_workflows(), ids=workflow_id)
def test_workflow(workflow_file):
    """Test that example workflow passes schema validation, generation, and dagfactory validation."""
    # Convert absolute path to relative path from workspace root
    relative_workflow = workflow_file.relative_to(WORKSPACE_ROOT)

    # Step 1: Schema validation
    result = subprocess.run(
        [
            sys.executable,
            "scripts/workflow_schema_validation/main.py",
            str(relative_workflow),
        ],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Schema validation failed:\n"
        f"{'='*60}\n"
        f"{result.stderr or result.stdout}\n"
        f"{'='*60}"
    )

    # Step 2: Workflow generation
    result = subprocess.run(
        [sys.executable, "scripts/workflow_generator/main.py", str(relative_workflow)],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, "PYTHONPATH": "airflow"},
    )

    assert result.returncode == 0, (
        f"Workflow generation failed:\n"
        f"{'='*60}\n"
        f"{result.stderr or result.stdout}\n"
        f"{'='*60}"
    )

    # Step 3: Validate generated workflow
    parts = str(relative_workflow).split("/")
    environment, project, workflow = parts[1], parts[2], parts[3]

    # The generator may rename projects, so check for any aliases
    project = PROJECT_ALIASES.get(project, project)

    dist_dir = WORKSPACE_ROOT / "dist" / "dags" / environment / project / workflow
    yaml_file = dist_dir / "workflow.yml"
    python_file = dist_dir / "dag.py"

    is_python_dag = python_file.exists()
    dist_file = python_file if is_python_dag else yaml_file

    if is_python_dag:
        # For Python DAGs, try to import/execute it
        result = subprocess.run(
            [sys.executable, str(dist_file)],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "PYTHONPATH": "airflow"},
            timeout=30,
        )
    else:
        # For YAML DAGs, validate with dagfactory
        result = subprocess.run(
            [sys.executable, "scripts/workflow_validation/main.py", str(dist_file)],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "PYTHONPATH": "airflow"},
            timeout=30,
        )

    assert result.returncode == 0, (
        f"Workflow validation failed:\n"
        f"{'='*60}\n"
        f"{result.stderr or result.stdout}\n"
        f"{'='*60}"
    )
