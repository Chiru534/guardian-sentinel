import json
import os

notebook_path = 'phishing-e-mail-detection (1).ipynb'
output_path = 'notebook_code_extracted.py'

if not os.path.exists(notebook_path):
    print(f"Error: {notebook_path} not found.")
    exit(1)

with open(notebook_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

extracted_code = []
for cell in data.get('cells', []):
    if cell.get('cell_type') == 'code':
        source = cell.get('source', [])
        if isinstance(source, list):
            extracted_code.append("".join(source))
        else:
            extracted_code.append(source)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n\n# --- NEW CELL ---\n\n".join(extracted_code))

print(f"Successfully extracted code to {output_path}")
