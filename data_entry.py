import json
from termcolor import colored, cprint

with open('data/recipes.json', 'r') as f:
    db = json.load(f)
with open('data/powergen_recipes.json', 'r') as f:
    powergen_db = json.load(f)

prompt = lambda just="": input(colored(f'> {just}', 'green'))
while True:
    process_dict = {}

    print('Machine type ("exit" to exit)')
    user_in = prompt()
    if user_in == 'exit':
        break
    process_dict['m'] = user_in
    if user_in == 'crafting':
        process_dict['dur'] = 0
        process_dict['eut'] = 0
        process_dict['ma'] = 'S'
    elif user_in == 'electric furnace':
        process_dict['ma'] = 'LV'
        process_dict['eut'] = 4
        process_dict['dur'] = 6
    elif user_in in {'gas turbine', 'steam turbine', 'combustion generator'}:
        process_dict['dur'] = 0
        process_dict['eut'] = 0
        process_dict['ma'] = 'LV'
    else:
        print('Minimum machine age')
        process_dict['ma'] = prompt()
        print('Duration')
        process_dict['dur'] = float(prompt())
        print('EU/t')
        process_dict['eut'] = float(prompt())

    inputs = []
    print('Inputs. Input as "10 my ingredient".')
    print('"n" goes to outputs.')
    while True:
        user_in = prompt(just="    ")
        if user_in == 'n':
            break
        words = user_in.split(' ')
        quant = float(words[0])
        ing = ' '.join(words[1:])
        inputs.append([ing, quant])
    process_dict['I'] = inputs

    outputs = []
    print('Outputs. Output as "10 my ingredient".')
    print('"n" goes to next recipe.')
    while True:
        user_in = prompt(just="    ")
        if user_in == 'n':
            break
        words = user_in.split(' ')
        quant = float(words[0])
        ing = ' '.join(words[1:])
        outputs.append([ing, quant])
    process_dict['O'] = outputs

    print()
    db.append(process_dict)
    powergen_db.append(process_dict)

    with open('data/recipes.json', 'w') as f:
        json.dump(db, f, indent=4)
    with open('data/powergen_recipes.json', 'w') as f:
        json.dump(powergen_db, f, indent=4)