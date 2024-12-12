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

import rclpy
from rclpy.node import Node
from api_calls import generate_sequence_module
from asset_mapper import process_module_sequence
from pose_fetcher import process_pose_sequence, load_containers_dict
import yaml
import os
from std_msgs.msg import String

class NLP(Node):
    def __init__(self):
        super().__init__("nlp_node")
        self.get_logger().info("NLP NODE INIT")
        self.create_subscription(String, '/nlp', self.input_callback, 10)
    
    def input_callback(self, msg):
        user_input = msg.data

        module_sequence = generate_sequence_module(user_input)
        print("\nGenerated Module Sequence:")
        print(module_sequence)
        print()

        # Define the path to the container assets CSV file
        # Adjust the path as per your operating system
        container_csv_path = os.path.join('container_assets.csv')

        # Load container data from CSV file
        containers_dict = load_containers_dict(container_csv_path)
        containers_list = list(containers_dict.values())

        # Process the module sequence to map containers
        final_module_sequence, relevant_container_ids = process_module_sequence(module_sequence, containers_list)
        print("Final Module Sequence:")
        print(final_module_sequence)
        print()

        # Process the module sequence to calculate positions
        pose_sequence = process_pose_sequence(final_module_sequence, containers_dict)

        # Define the output YAML file path
        output_yaml_path = os.path.join('/ras_sim_lab/ros2_ws/src/ras_bt_framework/7.yaml')  # You can change the path as needed
        # Write the pose sequence to the YAML file
        try:
            with open(output_yaml_path, 'w') as yaml_file:
                yaml.dump(pose_sequence, yaml_file, sort_keys=False)
            print(f"Pose sequence has been written to '{output_yaml_path}'")
        except Exception as e:
            print(f"Error writing to YAML file: {e}")

def main():
    rclpy.init(args=None)
    node = NLP()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    exit()


if __name__ == "__main__":
    main()
