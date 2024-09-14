import json

def write_file(fname, content):
    with open(fname, "w") as f:
        f.write(content)

def write_json_file(fname, json_str: str):
    # replace any ' with "
    json_str = json_str.replace("'", '"')

    # safely convert the JSON string to a python object
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    # write the Python Object to the file as JSON
    with open(fname, "w") as f:
        json.dump(data, f, indent=4)
