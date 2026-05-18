import json

with open('../../registry/registry.json', 'r') as f:
    data = json.load(f)

js_code = "const FLEET_REGISTRY = [\n"
for sat in data.get('satellites', []):
    id_ = sat.get('sheet_id') or sat.get('id')
    name_ = (sat.get('name') or 'Unknown Satellite').replace("'", "\\'")
    if id_:
        js_code += f"  {{ id: '{id_}', name: '{name_}' }},\n"
js_code += "];\n"

with open('Fleet_Registry.gs', 'w') as f:
    f.write(js_code)
print("Generated Fleet_Registry.gs")
