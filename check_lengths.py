import re
lines = open('backend/src/main/resources/data.sql', 'r', encoding='utf-8').readlines()
max_name = 0
max_desc = 0
for line in lines:
    if line.startswith('MERGE INTO products'):
        # Extract name between first two single-quoted strings
        parts = re.findall(r"'((?:[^']|'')*)'", line)
        if len(parts) >= 1:
            max_name = max(max_name, len(parts[0]))
        if len(parts) >= 3:
            max_desc = max(max_desc, len(parts[2]))
print(f"Max product name length: {max_name}")
print(f"Max description length: {max_desc}")
