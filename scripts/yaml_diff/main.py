import yaml
from deepdiff import DeepDiff
import sys

# Ensure the correct number of arguments are provided
if len(sys.argv) != 3:
    print("Usage: python main.py <path_to_yaml_main> <path_to_yaml_pr>")
    sys.exit(1)

# Get file paths from command-line arguments
yaml_main_path = sys.argv[1]
yaml_pr_path = sys.argv[2]

# Load YAML data from files
try:
    with open(yaml_main_path, "r", encoding="utf-8") as main_file:
        main_data = yaml.safe_load(main_file)
except FileNotFoundError:
    print(f"Error: File not found - {yaml_main_path}")
    sys.exit(1)

try:
    with open(yaml_pr_path, "r", encoding="utf-8") as pr_file:
        pr_data = yaml.safe_load(pr_file)
except FileNotFoundError:
    print(f"Error: File not found - {yaml_pr_path}")
    sys.exit(1)

# Compare the data
diff = DeepDiff(main_data, pr_data, ignore_order=True)

# Check for changes in the entire file
if diff:
    # Check if the only change is in `dag.tag`
    dag_tag_changes = diff.get('values_changed', {}).get("root['dag']['tag']", None)
    other_changes = any(
        key != "root['dag']['tag']"
        for key in diff.get('values_changed', {}).keys()
    )
    additions = diff.get('dictionary_item_added', None)
    removals = diff.get('dictionary_item_removed', None)
    iterable_item_added = diff.get('iterable_item_added', None)
    iterable_item_removed = diff.get('iterable_item_removed', None)
    type_changes = diff.get('type_changes', None)
    set_item_added = diff.get('set_item_added', None)
    set_item_removed = diff.get('set_item_removed', None)

    if (
        other_changes or additions or removals or iterable_item_added or
        iterable_item_removed or type_changes or set_item_added or set_item_removed
    ):
        print("Warning: Changes detected outside dag.tag")
        print(f"Differences: {diff}")
    elif dag_tag_changes:
        print("Only dag.tag has changed")
    else:
        print("No changes detected in dag.tag")
else:
    print("No changes detected in the file")
