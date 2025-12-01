import json


def convert_to_django_dump(json_data):
    """
    Converts JSON data into a Django dump-like format.

    Args:
        json_data: A list of JSON objects representing tasks.

    Returns:
        A list of Django dump-like objects.
    """

    django_dump_data = []
    for task in json_data:
        dump_data = {
            "model": "tasks.Task",  # Replace 'tasks' with your app name
            "pk": task["id"],
            "fields": {
                "category_id": task["category_id"],
                "context": task["context"],
                "initial_code": task["initialCode"],
                "level": task["level"],
                "next_task_id": task["nextTask_id"],
                "open_code": task["openCode"],
                "phase_id": task["phase_id"],
                "points": task["points"],
                "title": task["title"],
            },
        }
        django_dump_data.append(dump_data)

    return django_dump_data


# Load your JSON data
with open("tasks_task.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

# Convert to Django dump format
django_dump = convert_to_django_dump(json_data)

# Print or save the Django dump format
print(json.dumps(django_dump, indent=4))
# Save the Django dump format to a new file
with open("django_dump_test.json", "w", encoding="utf-8") as f:
    json.dump(django_dump, f, indent=4)
