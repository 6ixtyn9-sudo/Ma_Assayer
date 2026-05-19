import re

file_path = "docs/MODULE 01_Output_Writers"
with open(file_path, "r") as f:
    content = f.read()

content = content.replace("// source  (Side|Totals)", "// source  (Side|Totals|Other)")

with open(file_path, "w") as f:
    f.write(content)
print("Updated Output Writers")
