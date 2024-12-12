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

from openai import OpenAI
import json
import os

MODEL = "gpt-4o-2024-08-06"
PATH = os.path.join(os.environ["RAS_WORKSPACE_PATH"], "src" , "ras_tasklingo", "config", "openai.json")

def generate_sequence_module(input):
    with open(PATH) as f:
      key_data = json.load(f)
    client = OpenAI(api_key=key_data["OPEN_API_KEY"])
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are an AI assistant that converts natural language instructions into a sequence of module calls with appropriate parameters.

**Available Modules:**

1. **pick**:
   - **Parameters**:
     - container: A dictionary with the following keys:
       - type: The type of container (e.g., "beaker", "test tube").
       - size: Any size information if provided; otherwise, "null"
       - content name: Name of the contents (e.g., "copper sulphate solution", "distilled water", "concentrated sulphuric acid") if specified, otherwise "null"; common name of a chemical. (**note: "null" is not the same as "empty", treat "empty" as a content name. Never add a description like a color in content name)
       - content color: Color of the contents (e.g., "blue") if specified, otherwise "null"
       - content volume: Volume of the content if specified, otherwise "null"
       - landmark: A landmark if specified; otherwise "null".
   - **Usage**:

pick(container={type: ..., size: ..., content name: ..., content color: ..., content volume: ..., landmark: ...})

2. **pour**:
   - **Parameters**:
     - original_container: A dictionary similar to the container in pick.
     - destination_container: A dictionary for the destination container. Use "active container" if not specified.
     - volume: The volume to pour; use "all" if not specified.
   - **Usage**:

pour(original_container={...}, destination_container={...}, volume=...)

3. **place**:
   - **Parameters**:
     - container: A dictionary similar to the container in pick.
     - destination_location: The destination location if an (x, y, z) coordinate is provided; otherwise, "none".
     - landmark: A landmark if specified; otherwise "null".
   - **Usage**:

place(container={...}, destination_location=..., landmark=...)

=
**Instructions:**

- **Extract as much information as possible** from the input instruction to fill the parameters.
- **If a parameter is not specified**, use the default values as described.
- **Do not query any external data sources**; rely solely on the input instruction.
- **Handle negations** appropriately. If an action is negated in the instruction (e.g., "Do not pour"), do not include that module in the sequence.
- **Sequence the modules** in the order that makes sense based on the instruction.
"""
            },
            {"role": "user", "content": str(input)}
        ]
    )
    return completion.choices[0].message.content

# Example usage:
# x = generate_sequence_module("Pick up the beaker with blue solution. Place it at (1,2,3)")
# print(x)
