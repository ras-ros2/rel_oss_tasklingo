"""
Copyright (C) 2024 Harsh Davda

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

For inquiries or further information, you may contact:
Harsh Davda
Email: info@opensciencestack.org
"""

import csv
import re

# Function to parse module calls
def parse_module_call(module_call_str):
    try:
        # Extract the function name and parameters
        match = re.match(r'(\w+)\((.*)\)$', module_call_str.strip(), re.DOTALL)
        if not match:
            print(f"Error parsing module call '{module_call_str}': Invalid format")
            return None, {}
        func_name = match.group(1)
        params_str = match.group(2)

        # Split parameters at the top level
        param_list = split_top_level(params_str)
        params = {}
        for param in param_list:
            if '=' not in param:
                continue
            key, value = param.split('=', 1)
            key = key.strip()
            value = value.strip()
            # Parse the value
            parsed_value = parse_value(value)
            params[key] = parsed_value
        return func_name, params
    except Exception as e:
        print(f"Error parsing module call '{module_call_str}': {e}")
        return None, {}

# Function to split parameters at the top level
def split_top_level(s):
    result = []
    bracket_level = 0
    current = ''
    idx = 0
    while idx < len(s):
        c = s[idx]
        if c in '([{':
            bracket_level += 1
        elif c in ')]}':
            bracket_level -= 1
        if c == ',' and bracket_level == 0:
            result.append(current)
            current = ''
        else:
            current += c
        idx += 1
    if current:
        result.append(current)
    return result

# Function to parse individual values
def parse_value(value_str):
    value_str = value_str.strip()
    # Handle dictionaries
    if value_str.startswith('{') and value_str.endswith('}'):
        return parse_dict(value_str)
    # Handle tuples or lists
    elif value_str.startswith('(') and value_str.endswith(')'):
        return parse_tuple(value_str)
    elif value_str.startswith('[') and value_str.endswith(']'):
        return parse_list(value_str)
    # Handle strings
    elif (value_str.startswith("'") and value_str.endswith("'")) or (value_str.startswith('"') and value_str.endswith('"')):
        # Remove outer quotes
        value_str = value_str[1:-1].strip()
        # After stripping quotes, check for nested structures
        if value_str.startswith('{') and value_str.endswith('}'):
            return parse_dict(value_str)
        elif value_str.startswith('(') and value_str.endswith(')'):
            return parse_tuple(value_str)
        elif value_str.startswith('[') and value_str.endswith(']'):
            return parse_list(value_str)
        else:
            return value_str
    # Handle numbers
    else:
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            return value_str  # Return as string if not a number

# Function to parse dictionaries
def parse_dict(dict_str):
    dict_str = dict_str.strip()[1:-1].strip()  # Remove braces
    items = split_top_level(dict_str)
    result = {}
    for item in items:
        if ':' not in item:
            continue
        key, value = item.split(':', 1)
        # Remove quotes from keys and replace spaces with underscores
        key = key.strip().strip('"').strip("'").replace(' ', '_')
        value = value.strip()
        result[key] = parse_value(value)
    return result

# Function to parse tuples
def parse_tuple(tuple_str):
    tuple_str = tuple_str.strip()[1:-1].strip()  # Remove parentheses
    items = split_top_level(tuple_str)
    return tuple(parse_value(item) for item in items)

# Function to parse lists
def parse_list(list_str):
    list_str = list_str.strip()[1:-1].strip()  # Remove brackets
    items = split_top_level(list_str)
    return [parse_value(item) for item in items]

# Function to match container descriptions to actual containers
def match_container(container_desc, containers):
    # Remove fields with value 'null' or None
    criteria = {k: v for k, v in container_desc.items() if v != 'null' and v is not None}
    matching_containers = []
    for container in containers:
        match = all(
            str(container.get(key, '')).lower() == str(value).lower()
            for key, value in criteria.items()
        )
        if match:
            matching_containers.append(container)
    if len(matching_containers) == 1:
        return matching_containers[0]
    elif len(matching_containers) == 0:
        return None
    else:
        # Multiple matches; select the first one or implement additional logic
        return matching_containers[0]

# Function to split module calls considering nested parentheses
def split_module_calls(s):
    result = []
    idx = 0
    n = len(s)
    while idx < n:
        # Skip any whitespace
        while idx < n and s[idx].isspace():
            idx += 1
        if idx >= n:
            break
        # Check if this is a function name
        func_name = ''
        start_idx = idx
        while idx < n and (s[idx].isalpha() or s[idx] == '_'):
            func_name += s[idx]
            idx += 1
        if not func_name:
            idx += 1
            continue
        # Skip any whitespace
        while idx < n and s[idx].isspace():
            idx += 1
        if idx >= n or s[idx] != '(':
            # Not a function call, continue searching
            continue
        # Now we've got a function name followed by '('
        bracket_level = 0
        current = ''
        while idx < n:
            c = s[idx]
            current += c
            if c == '(':
                bracket_level += 1
            elif c == ')':
                bracket_level -= 1
                if bracket_level == 0:
                    idx += 1
                    break
            idx += 1
        result.append(func_name + current)
    return result

# Function to process module sequence
def process_module_sequence(module_sequence, containers):
    """
    Processes the module sequence by mapping container descriptions to actual container IDs.

    Args:
        module_sequence (str): The raw module sequence string.
        containers (list): List of container dictionaries loaded from the CSV.

    Returns:
        tuple: (final_module_sequence (str), relevant_container_ids (list))
    """
    # Split the module sequence into individual module calls
    module_calls = split_module_calls(module_sequence)
    updated_module_sequence = ""
    relevant_container_ids = []
    for module_call in module_calls:
        module_name, params = parse_module_call(module_call)
        if not module_name:
            continue  # Skip if parsing failed
        # Process the parameters
        if module_name.lower() == "pour":
            # Handle pour separately
            original_container_desc = params.get('original_container', {})
            destination_container_desc = params.get('destination_container', {"type": "active container"})
            volume = params.get('volume', "all")
            
            # Map original_container
            matching_original = match_container(original_container_desc, containers)
            if matching_original:
                original_id = matching_original['id']
                relevant_container_ids.append(original_id)
            else:
                print(f"No matching original_container found for pour in module '{module_call}'")
                original_id = 'unknown'
            
            # Map destination_container
            matching_destination = match_container(destination_container_desc, containers)
            if matching_destination:
                destination_id = matching_destination['id']
                relevant_container_ids.append(destination_id)
            else:
                # Handle "active container" if destination_container is not specified
                if destination_container_desc.get('type', '').lower() == "active container":
                    destination_id = 'active_container'
                else:
                    print(f"No matching destination_container found for pour in module '{module_call}'")
                    destination_id = 'unknown'
            
            # Handle volume
            if isinstance(volume, (int, float)):
                volume_str = str(volume)
            elif isinstance(volume, str):
                volume_str = volume
            else:
                volume_str = 'all'
            
            # Format the pour command
            if volume_str != "all":
                updated_module_sequence += f"pour({original_id},{destination_id},{volume_str})\n"
            else:
                updated_module_sequence += f"pour({original_id},{destination_id})\n"
        else:
            # Handle pick and place
            for param_name, param_value in params.items():
                if param_name in ['container', 'original_container', 'destination_container']:
                    matching_container = match_container(param_value, containers)
                    if matching_container:
                        params[param_name] = {
                            'id': matching_container['id'],
                            'aruco_id': str(matching_container['aruco_id']),
                        }
                        relevant_container_ids.append(matching_container['id'])
                    else:
                        print(f"No matching container found for {param_name} in {module_name}")
                        params[param_name] = {'id': 'unknown', 'aruco_id': 'unknown'}
            # Format the module call in the desired format
            if module_name.lower() == "pick":
                container_id = params['container']['id']
                updated_module_sequence += f"Pick({container_id})\n"
            elif module_name.lower() == "place":
                container_id = params['container']['id']
                destination_location = params.get('destination_location', 'none')
                # Convert destination_location to string without extra quotes
                if isinstance(destination_location, (tuple, list)):
                    destination_location_str = '(' + ','.join(map(str, destination_location)) + ')'
                else:
                    destination_location_str = str(destination_location)
                updated_module_sequence += f"Place({container_id},{destination_location_str})\n"
    return updated_module_sequence.strip(), relevant_container_ids
