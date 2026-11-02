"""Exit 0 if every changed field matches a "field=new_value" rule in policy.yml, otherwise exit 1.

Usage: python scripts/automatic_approval/main.py <main workflow.yml> <PR workflow.yml>
"""
import re
import sys
import yaml


def flatten(data, prefix=""):
    """Turn nested YAML into dotted fields: {"dag": {"tag": "1"}} -> {"dag.tag": "1"}."""
    if not isinstance(data, dict) or not data:
        return {prefix[:-1]: data}
    fields = {}
    for key, value in data.items():
        fields.update(flatten(value, f"{prefix}{key}."))
    return fields


def get_rules(policy, workflow):
    """Rules from default + non_prod/prod + matching overrides. Returns None if a group says manual: true."""
    environment = workflow.split("/")[1]
    rules = list(policy["default"]["allowed"])
    for group in [policy.get("non_prod"), policy.get("prod"), *(policy.get("overrides") or [])]:
        if not group:
            continue
        if environment in group.get("environments", []) or re.fullmatch(group.get("match", "$^"), workflow):
            if group.get("manual"):
                return None
            rules += group.get("allowed", [])
    return rules


if __name__ == "__main__":
    policy = yaml.safe_load(open("scripts/automatic_approval/policy.yml"))
    old = flatten(yaml.safe_load(open(sys.argv[1])))
    new = flatten(yaml.safe_load(open(sys.argv[2])))
    workflow = sys.argv[2].rsplit("/", 1)[0]
    rules = get_rules(policy, workflow)

    changed = [field for field in sorted(set(old) | set(new)) if old.get(field) != new.get(field)]
    blocked = []
    for field in changed:
        change = f"{field}={new.get(field)}"
        if rules is None or not any(re.fullmatch(rule, change, re.DOTALL) for rule in rules):
            blocked.append(field)

    print(f"Workflow: {workflow}")
    print(f"Changed: {', '.join(changed) or 'none'}")
    print(f"Needs a human: {', '.join(blocked) or 'none'}")
    sys.exit(1 if blocked else 0)
