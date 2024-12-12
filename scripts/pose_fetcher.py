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
import yaml
import math

def split_args(s):
    """
    Splits a string into arguments, considering nested parentheses and quotes.

    Args:
        s (str): The string to split.

    Returns:
        list: List of argument strings.
    """
    args = []
    current_arg = ''
    bracket_level = 0
    in_quotes = False
    quote_char = ''
    for c in s:
        if c in ('"', "'"):
            if in_quotes and c == quote_char:
                in_quotes = False
            elif not in_quotes:
                in_quotes = True
                quote_char = c
        elif not in_quotes:
            if c == ',' and bracket_level == 0:
                args.append(current_arg.strip())
                current_arg = ''
                continue
            elif c == '(':
                bracket_level +=1
            elif c == ')':
                bracket_level -=1
        current_arg += c
    if current_arg:
        args.append(current_arg.strip())
    return args

def process_pose_sequence(module_sequence, containers_dict):
    """
    Processes the final module sequence to generate pose sequences and targets.

    Args:
        module_sequence (str): The final module sequence string.
        containers_dict (dict): Dictionary of containers loaded from the CSV.

    Returns:
        dict: Dictionary containing 'Poses' and 'targets' for YAML output.
    """
    # Parse the module sequence into a list of module calls
    module_calls = [line.strip() for line in module_sequence.strip().split('\n') if line.strip()]

    # Initialize pose and target lists
    pose_sequence = {}
    targets = []
    pose_counter = 1  # To generate unique pose labels

    for module_call in module_calls:
        if module_call.startswith('Pick(') and module_call.endswith(')'):
            # Extract the container_id
            content = module_call[len('Pick('):-1].strip()
            container_id = content
            # Get the current position and orientation of the container
            container = containers_dict.get(container_id)
            if container:
                position = container['position']
                orientation = container['orientation']
                # If orientation is missing or incomplete, use default quaternion
                if len(orientation) < 4:
                    orientation = [0.0, 0.0, 0.0, 1.0]
                # Convert quaternion to roll, pitch, yaw
                roll, pitch, yaw = quaternion_to_euler(orientation)
                # Create pose label
                pose_label = f"pose{pose_counter}"
                pose_counter +=1
                # Add pose to sequence
                pose_sequence[pose_label] = {
                    'x': round(position[0], 3),
                    'y': round(position[1], 3),
                    'z': round(position[2], 3),
                    'roll': round(roll, 3),
                    'pitch': round(pitch, 3),
                    'yaw': round(yaw, 3)
                }
                # Add to targets
                targets.append(pose_label)
                targets.append('grasp')
            else:
                error_msg = f"Error: Container {container_id} not found."
                print(error_msg)
                # Optionally, you can handle errors differently
                pose_sequence[f"error_pose{pose_counter}"] = {'error': error_msg}
                pose_counter +=1
        elif module_call.startswith('Place(') and module_call.endswith(')'):
            # Extract the arguments
            content = module_call[len('Place('):-1].strip()
            # Use split_args to split arguments
            args = split_args(content)
            if len(args) < 2:
                print(f"Error: Insufficient arguments for Place in module call '{module_call}'")
                continue
            container_id = args[0]
            position_str = args[1]
            position_str = position_str.strip('()')
            try:
                new_position = [float(x.strip()) for x in position_str.split(',')]
            except ValueError:
                print(f"Error: Invalid position format in Place module call '{module_call}'")
                continue
            # Check if orientation is specified
            if len(args) > 2:
                orientation_str = args[2]
                orientation_str = orientation_str.strip('()')
                try:
                    new_orientation = [float(x.strip()) for x in orientation_str.split(',')]
                except ValueError:
                    print(f"Error: Invalid orientation format in Place module call '{module_call}'")
                    new_orientation = [0.0, 0.0, 1.0]  # Default orientation
            else:
                # Use default orientation if not specified
                new_orientation = [0.0, 0.0, 1.0]  # roll, pitch, yaw
            # Update the container's position and orientation
            container = containers_dict.get(container_id)
            if container:
                container['position'] = new_position
                # If orientation is provided as roll, pitch, yaw, store them directly
                if len(new_orientation) == 3:
                    roll, pitch, yaw = new_orientation
                elif len(new_orientation) == 4:
                    # If provided as quaternion, convert to Euler angles
                    roll, pitch, yaw = quaternion_to_euler(new_orientation)
                else:
                    # Default orientation
                    roll, pitch, yaw = 0.0, 0.0, 1.0
                container['orientation'] = new_orientation  # Update orientation
                # Create pose label
                pose_label = f"pose{pose_counter}"
                pose_counter +=1
                # Add pose to sequence
                pose_sequence[pose_label] = {
                    'x': round(new_position[0], 3),
                    'y': round(new_position[1], 3),
                    'z': round(new_position[2], 3),
                    'roll': round(roll, 3),
                    'pitch': round(pitch, 3),
                    'yaw': round(yaw, 3)
                }
                # Add to targets
                targets.append(pose_label)
                targets.append('release')
            else:
                error_msg = f"Error: Container {container_id} not found."
                print(error_msg)
                # Optionally, handle error
                pose_sequence[f"error_pose{pose_counter}"] = {'error': error_msg}
                pose_counter +=1
        elif module_call.startswith('pour(') and module_call.endswith(')'):
            # Extract the arguments
            content = module_call[len('pour('):-1].strip()
            args = split_args(content)
            if len(args) < 2:
                print(f"Error: Insufficient arguments for pour in module call '{module_call}'")
                continue
            original_id = args[0]
            destination_id = args[1]
            volume = args[2] if len(args) > 2 else 'all'
            # Get original container's position and orientation
            destination_container = containers_dict.get(destination_id)
            if destination_container:
                position = destination_container['position']
                orientation = destination_container['orientation']
                # Convert quaternion to roll, pitch, yaw if needed
                if len(orientation) < 4:
                    orientation = [0.0, 0.0, 0.0, 1.0]
                roll, pitch, yaw = quaternion_to_euler(orientation)
                # Create pose label
                pose_label = f"pose{pose_counter}"
                pose_counter +=1
                # Add pose to sequence
                pose_sequence[pose_label] = {
                    'x': round(position[0], 3),
                    'y': round(position[1], 3),
                    'z': round(position[2], 3),
                    'roll': round(roll, 3),
                    'pitch': round(pitch, 3),
                    'yaw': round(yaw, 3)
                }
                # Add to targets
                targets.append(pose_label)
                # Handle rotation value
               
                targets.append(float(1.57))  
                targets.append(float(-1.57))
            else:
                error_msg = f"Error: Original container {original_id} not found."
                print(error_msg)
                pose_sequence[f"error_pose{pose_counter}"] = {'error': error_msg}
                pose_counter +=1

            # Destination pose can be handled similarly if needed
            # For simplicity, assuming pour only requires original pose and rotate action
        else:
            error_msg = f"Error: Unknown module call '{module_call}'"
            print(error_msg)
            # Optionally, handle error
            pose_sequence[f"error_pose{pose_counter}"] = {'error': error_msg}
            pose_counter +=1

    # Prepare the final YAML structure
    final_output = {
        'Poses': pose_sequence,
        'targets': targets
    }

    return final_output

def quaternion_to_euler(q):
    """
    Convert a quaternion into Euler angles (roll, pitch, yaw).

    Args:
        q (list or tuple): Quaternion [qx, qy, qz, qw].

    Returns:
        tuple: (roll, pitch, yaw) in radians.
    """
    qx, qy, qz, qw = q

    # Roll (x-axis rotation)
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (qw * qy - qz * qx)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  # use 90 degrees if out of range
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (qw * qz + qx * qy)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    # If desired, convert radians to degrees
    # roll = math.degrees(roll)
    # pitch = math.degrees(pitch)
    # yaw = math.degrees(yaw)

    # Adding default orientation if not provided
    if not (roll or pitch or yaw):
        roll, pitch, yaw = 0.0, 0.0, 1.0

    return roll, pitch, yaw

# Function to load containers from CSV and return as a dictionary
def load_containers_dict(container_csv_path):
    """
    Loads container data from a CSV file into a dictionary.

    Args:
        container_csv_path (str): Path to the container assets CSV file.

    Returns:
        dict: Dictionary with container IDs as keys and container attributes as values.
    """
    containers_dict = {}
    with open(container_csv_path, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            container_id = row['id']
            # Store position as a list of floats
            position_str = row['position']
            # Remove square brackets and split by comma
            position_list = position_str.strip('[]').split(',')
            try:
                position = [float(x.strip()) for x in position_list]
            except ValueError:
                print(f"Error: Invalid position format for container '{container_id}'")
                position = [0.0, 0.0, 0.0]  # Default position

            # Similarly for orientation
            orientation_str = row['orientation']
            orientation_list = orientation_str.strip('[]').split(',')
            try:
                orientation = [float(x.strip()) for x in orientation_list]
            except ValueError:
                print(f"Error: Invalid orientation format for container '{container_id}'")
                orientation = [0.0, 0.0, 0.0, 1.0]  # Default quaternion

            # Store the container information
            containers_dict[container_id] = {
                'position': position,
                'orientation': orientation,
                'type': row.get('type', 'unknown'),
                'id': container_id,
                'aruco_id': row.get('aruco_id', 'unknown'),
                'content_name': row.get('content_name', 'null'),
                'content_volume': row.get('content_volume', 'null'),
                'content_color': row.get('content_color', 'null'),
                'active_status': row.get('active_status', 'null'),
                'landmark': row.get('landmark', 'null')
            }
    return containers_dict
