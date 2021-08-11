import json
import sys

with open('data/powergen_recipes.json', 'r') as f:
    db = json.load(f)

print(db[int(sys.argv[1])])