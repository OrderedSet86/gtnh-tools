# Standard libraries
import json
from collections import defaultdict, deque
from copy import deepcopy
from math import ceil
from pathlib import Path

# Pypi libraries
import networkx as nx
from ksuid import ksuid
from termcolor import colored, cprint

# Internal libraries
from core.utils import *

if __name__ == '__main__':
    recipes, input_lookup, output_lookup = loadRecipesAndTables(
        'data/recipes.json',
        'MV'
    )
    preferences_path = Path('data/preferences.json')
    if preferences_path.is_file():
        with open(preferences_path, 'r') as f:
            cached_preferences = json.load(f)
    else:
        cached_preferences = {}

    while True:
        # Input recipe to search
        cprint('Enter recipe to backtrack (ie "1 electronic circuit")', 'green')
        recipe_search = input(colored('> ', 'green'))

        words = recipe_search.split(' ')
        quant = int(words[0])
        recipe_search = ' '.join(words[1:])

        # Check validity
        if recipe_search in output_lookup:
            break
        else:
            cprint('Recipe not in output lookup table.', 'red')

    # Backtracking
    # Store recipe as a networkx digraph
    preferences = {} # output : preferred recipe # TODO
    stop_early = {
        'rubber bar',
        'glass tube'
        'wood plank',
        'raw rubber dust',
        'fluid - creosote oil',
        'fluid - water',
        'empty cell',
        'carbon dust',
        'diamond',
        'flint',
        'small sodium battery',
        'wrought iron plate'
    }
    all_item_count = defaultdict(int)
    total_EU = 0

    G = nx.DiGraph()
    stack = [
        (
            recipe_search, # targetted output
            quant, # quantity of target output
            None, # parent uuid
            0 # depth
        )
    ]
    leftover = defaultdict(int)
    basic_components = defaultdict(int)
    stack_output = []
    while stack:
        target_output, quantity, parent_id, depth = stack.pop()
        uuid = ksuid()

        all_item_count[target_output] += quantity

        # Check if exists in output table. If not, go to next node
        if target_output not in output_lookup or target_output in stop_early:
            basic_components[target_output] += quantity
            stack_output.append(f'{" "*depth}{quantity}x [{target_output}]')
            continue

        # If exists, disambiguate with user if multiple matches
        matching_recipes = [recipes[x] for x in output_lookup[target_output]]
        if len(matching_recipes) == 1:
            curr = matching_recipes[0]
        else:
            curr, cached_preferences = queryAlternatives(
                matching_recipes,
                target_output,
                cached_preferences
            )

        curr = deepcopy(curr) # So we can make modifications

        # Track side outputs for terminal output
        relevant_output = [x for x in curr['O'] if x[0] == target_output][0]
        rec_ing, rec_q = relevant_output

        # Modify recipe based on request quantity
        if rec_q >= quantity:
            multiplier = 1
        else:
            multiplier = ceil(quantity/rec_q)
            for i in range(len(curr['I'])):
                curr['I'][i][1] *= multiplier
            for i in range(len(curr['O'])):
                curr['O'][i][1] *= multiplier
            curr['dur'] *= multiplier
            relevant_output = [rec_ing, rec_q*multiplier]

        total_EU += curr['dur'] * curr['eut']

        side_outputs = [x for x in curr['O'] if x[0] != target_output]
        # Track outputs based on modified recipe
        if relevant_output[1] > quantity:
            leftover[relevant_output[0]] += relevant_output[1] - quantity
            relevant_output[1] = quantity

        for output in side_outputs:
            leftover[output[0]] += output[1]

        # Print informed output amount
        stack_output.append(f'{" "*depth}{relevant_output[1]}x [{relevant_output[0]}]')

        for output in curr['O']:
            G.add_nodes_from([
                (
                    uuid,
                    {
                        'type': 0,
                        'name': output[0],
                        'quantity': output[1]
                    }
                )
            ])

        if parent_id is not None:
            G.add_edges_from([
                (
                    uuid,
                    parent_id
                )
            ])

        stack.extend([(x[0], x[1], uuid, depth+2) for x in curr['I']])

    with open(preferences_path, 'w') as f:
        json.dump(cached_preferences, f, indent=4)

    for line in stack_output:
        print(line)

    if leftover:
        print()
        print('Side products:')
        for ing, quant in leftover.items():
            print(f'{quant}x [{ing}]')

    if basic_components:
        print()
        print('Basic components:')
        for ing, quant in basic_components.items():
            print(f'{quant}x [{ing}]')

    print()
    print('All item count')
    for item, quant in all_item_count.items():
        print(f'{quant}x [{item}]')

    print()
    print(f'Total EU: {total_EU}')

    # TODO: Output to graphviz
    # A = nx.drawing.nx_agraph.to_agraph(G)
    # A.layout(
    #     'dot'
    # )
    # A.draw('recipe_tree.png')