import json
from collections import defaultdict
from termcolor import colored, cprint
from jsmin import jsmin

def queryAlternatives(
        recipes,
        target_output,
        cached_preferences
    ):
    if target_output in cached_preferences:
        return cached_preferences[target_output], cached_preferences

    cprint(f'Pick intended recipe ({target_output})', 'green')
    while True:
        # Get selection
        for i, r in enumerate(recipes):
            print(f'{i+1} {r}')
        num_option = input(colored('> ', 'green'))

        # Confirm selection validity
        try:
            parts = num_option.split()
            num_option = int(parts[0])-1
            break
        except:
            cprint('Invalid input.', 'red')

    chosen_recipe = recipes[num_option]
    if len(parts) > 1 and parts[1] == 'k':
        # Keep this preference permanently
        # (as long as using cached preferences is on)
        cached_preferences[target_output] = chosen_recipe
    return chosen_recipe, cached_preferences


def loadRecipesAndTables(json_path, age):
    # Load recipe database
    with open(json_path, 'r') as f:
        recipes = json.loads(jsmin(f.read()))

    # Create quick lookup tables
    input_lookup = defaultdict(list)
    output_lookup = defaultdict(list)
    for i, recipe in enumerate(recipes):
        input_ingredients = [x[0] for x in recipe['I']]
        for ing in input_ingredients:
            input_lookup[ing].append(i)

        output_ingredients = [x[0] for x in recipe['O']]
        for ing in output_ingredients:
            output_lookup[ing].append(i)

    # Modify recipes depending on current age
    if age == 'MV':
        for i, r in enumerate(recipes):
            if r['m'] == 'pyrolyse oven':
                recipes[i]['dur'] *= 2
                recipes[i]['m'] = 'pyrolyse oven (50% eff)'

    return recipes, input_lookup, output_lookup