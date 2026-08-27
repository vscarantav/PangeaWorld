import os
import re

files = [
    r'c:\Users\vscaran\Desktop\DevProjects\PangeaWorld\PangeaWorld_architecture_and_instructions.md',
    r'c:\Users\vscaran\Desktop\DevProjects\PangeaWorld\frontend\public\map_prototype.html'
]

def replace_roads(content):
    # Case sensitive replacements to preserve capitalization
    content = re.sub(r'\broads\b', 'railroads', content)
    content = re.sub(r'\bRoads\b', 'Railroads', content)
    content = re.sub(r'\broad\b', 'railroad', content)
    content = re.sub(r'\bRoad\b', 'Railroad', content)
    content = re.sub(r'\bhasRoad\b', 'hasRailroad', content)
    return content

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = replace_roads(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

print("Replacement complete.")
