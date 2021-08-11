# Goal:
# Convert "LV distillery"
# to
# "distillery"
# "ma": "LV" # ma == min age

import json

with open('data/recipes.json', 'r') as f:
    data = json.load(f)

ages = {'LV', 'MV'}
for i, recipe in enumerate(data):
    machine = recipe['m']
    age = machine[:2]
    if age in ages:
        recipe['m'] = ' '.join(machine.split(' ')[1:])
        recipe['ma'] = age
    else:
        if machine == 'furnace':
            recipe['ma'] = 'LV'
            recipe['m'] = 'electric furnace'
            recipe['eut'] = 4
            recipe['dur'] = 6
        elif machine in {'crafting'}:
            recipe['ma'] = 'S'
        elif machine in {'gas turbine', 'combustion generator', 'steam turbine'}:
            recipe['ma'] = 'LV'
        else:
            print(f'Unrecognized age: {machine}')
            exit(1)

with open('data/recipes.json', 'w') as f:
    json.dump(data, f, indent=4)