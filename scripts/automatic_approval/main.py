"""Check a workflow.yml change: each changed field must match a "field=new_value" rule in policy.yml.
Usage: python scripts/automatic_approval/main.py <main workflow.yml> <PR workflow.yml>
Exit code: 0 = auto-approve, 1 = needs a human.
"""
import re
import sys
import yaml


def load(path):
    with open(path, encoding="utf-8") as file:
        return yaml.safe_load(file)


def flatten(data, prefix=""):
    """Turn nested YAML into dotted fields: {"dag": {"tag": "1"}} -> {"dag.tag": "1"}."""
    if isinstance(data, dict) and data:
        result = {}
        for key, value in data.items():
            result.update(flatten(value, f"{prefix}{key}."))
        return result
    return {prefix.rstrip("."): data}


def get_layers(policy, workflow):
    """Layers that apply: default, then non_prod or prod by environment, then matching overrides."""
    environment = workflow.split("/")[1]
    layers = [policy["non_prod"], policy["prod"], *policy.get("overrides", [])]
    return [policy["default"]] + [layer for layer in layers if environment in layer.get("environments", [])
                                  or re.fullmatch(layer.get("match", "$^"), workflow)]


def is_blocked(field, value, layers):
    """True if this change needs a human: a layer is manual, or no rule matches "field=new_value"."""
    if any(layer.get("manual") for layer in layers):
        return True
    rules = [rule for layer in layers for rule in layer.get("allowed", [])]
    return not any(re.fullmatch(rule, f"{field}={value}", re.DOTALL) for rule in rules)


if __name__ == "__main__":
    old, new = flatten(load(sys.argv[1])), flatten(load(sys.argv[2]))
    workflow = sys.argv[2].rsplit("/", 1)[0]
    layers = get_layers(load("scripts/automatic_approval/policy.yml"), workflow)
    changed = [field for field in sorted(set(old) | set(new)) if old.get(field) != new.get(field)]
    blocked = [field for field in changed if is_blocked(field, new.get(field), layers)]
    print(f"Workflow: {workflow}\nChanged: {', '.join(changed) or 'none'}")
    print(f"Needs a human: {', '.join(blocked) or 'none'}")
    sys.exit(1 if blocked else 0)
