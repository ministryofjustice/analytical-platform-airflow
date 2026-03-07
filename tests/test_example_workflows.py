#!/usr/bin/env python3
"""
Unit tests for example workflows.
Ensures that all example workflows can be successfully generated and validated.
"""
import sys
import os
import subprocess
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = Path(
    os.getenv(
        "EXAMPLES_DIR",
        WORKSPACE_ROOT / "environments" / "development" / "analytical-platform",
    )
)


def find_example_workflows():
    """Find all example workflow files."""
    example_dirs = sorted(EXAMPLES_DIR.glob("example-*"))
    workflows = []
    for example_dir in example_dirs:
        workflow_file = example_dir / "workflow.yml"
        if workflow_file.exists():
            workflows.append(workflow_file)
    return workflows


def workflow_id(workflow_file):
    """Generate a readable test ID from the workflow file path."""
    return workflow_file.parent.name


@pytest.mark.parametrize("workflow_file", find_example_workflows(), ids=workflow_id)
def test_example_workflow(workflow_file):
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
    relative_path = workflow_file.relative_to(WORKSPACE_ROOT / "environments")
    yaml_file = WORKSPACE_ROOT / "dist" / "dags" / relative_path.parent / "workflow.yml"
    python_file = WORKSPACE_ROOT / "dist" / "dags" / relative_path.parent / "dag.py"

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
