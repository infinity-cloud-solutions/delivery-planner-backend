import csv
import json
import decimal

def parse_nested_field(field_value):
    """
    Parse a nested field (maps or lists) from string representation to the appropriate Python object.
    This function assumes the nested fields are in JSON-like string format.
    """
    try:
        return json.loads(field_value)
    except (ValueError, TypeError):
        return field_value

def convert_to_decimal(value):
    """
    Convert float strings to decimal.Decimal if valid; otherwise return the value as-is.
    """
    try:
        return decimal.Decimal(value)
    except (decimal.InvalidOperation, ValueError, TypeError):
        print(f"Value illegal {value}")
        return value

def clean_dynamodb_json(dynamo_json):
    """
    Recursively clean up DynamoDB JSON format to standard JSON format.
    """
    if isinstance(dynamo_json, dict):
        if len(dynamo_json) == 1:
            key, value = next(iter(dynamo_json.items()))
            if key == 'S':
                return value
            elif key == 'N':
                return convert_to_decimal(value)
            elif key == 'BOOL':
                return value
            elif key == 'M':
                return {k: clean_dynamodb_json(v) for k, v in value.items()}
            elif key == 'L':
                return [clean_dynamodb_json(item) for item in value]
        return {k: clean_dynamodb_json(v) for k, v in dynamo_json.items()}
    elif isinstance(dynamo_json, list):
        return [clean_dynamodb_json(item) for item in dynamo_json]
    else:
        return dynamo_json

def transform_row(row):
    """
    Apply specific transformations to the row.
    - Change 'status' from 'Programada' to 'Creada'
    - Set 'delivery_sequence' and 'cooler' to None
    - Convert 'longitude' and 'latitude' to decimal.Decimal if valid
    """
    if 'status' in row and row['status'] == 'Programada':
        row['status'] = 'Creada'
    row['delivery_sequence'] = None
    row['cooler'] = None
    if 'longitude' in row:
        row['longitude'] = convert_to_decimal(row['longitude'])
    if 'latitude' in row:
        row['latitude'] = convert_to_decimal(row['latitude'])
    return row

csv_file_path = 'selected.csv'
json_data = []

with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        parsed_row = {key: parse_nested_field(value) for key, value in row.items()}
        transformed_row = transform_row(parsed_row)
        cleaned_row = {key: clean_dynamodb_json(value) for key, value in transformed_row.items()}
        json_data.append(cleaned_row)

# Optionally save the JSON data to a file for verification
with open('data.json', 'w') as json_file:
    json.dump(json_data, json_file, indent=4, default=str)

print(json_data)  # You can print to verify the data
