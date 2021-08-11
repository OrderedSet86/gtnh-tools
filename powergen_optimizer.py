import math
import time
from collections import defaultdict, Counter, deque
from copy import deepcopy

from termcolor import cprint

from core.utils import *

# Idea:
# Given a list of farms with I/O rates,
# determine two things for each power tier:
# Most efficient EU generator (best EU/minute of human time)
# Highest EU/t generation

# First:
# Calculate net EU without adding additional farm sources



def printIng(quant, name):
    if math.isclose(quant, 0):
        return
    if math.isclose(quant, math.floor(quant)):
        quant = int(quant)

    if name == 's':
        cprint(
            f'    {quant} {name}',
            ['red', 'green'][quant < 0]
        )
    else:
        cprint(
            f'    {quant} {name}',
            ['green', 'red'][quant < 0]
        )


def updateInventory(
        inventory,
        recipe,
        recipe_index,
        DEBUG=False
    ):
    # Check if recipe can be applied (all items available in inventory)
    multiplier = 1
    multiplier_changed = False
    for inp in recipe['I']:
        name, quant = inp
        if name in inventory:
            if inventory[name] > 0.1:
                possible_new_multiplier = inventory[name] / quant
                if possible_new_multiplier > multiplier:
                    if not multiplier_changed:
                        multiplier = possible_new_multiplier
                elif possible_new_multiplier < multiplier:
                    multiplier = min(multiplier, possible_new_multiplier)
        multiplier_changed = True

    if DEBUG:
        print(f'{multiplier}x {recipe["m"]} ({recipe["ma"]} - {recipe_index})')
    if DEBUG >= 2:
        print('   ', inventory)
    # Perform actual inventory subtraction
    for inp in recipe['I']:
        name, quant = inp
        subing = -quant * multiplier
        inventory[name] += subing
        if DEBUG:
            printIng(subing, name)

    # Subtract machine EU from inventory, add time
    subEU = recipe['dur'] * -recipe['eut'] * 20 * multiplier
    subtime = recipe['dur'] * multiplier
    inventory['EU'] += subEU
    inventory['time'] += subtime
    if DEBUG:
        printIng(subEU, 'EU')
        printIng(subtime, 's')

    # Now that recipe is applied, add outputs to inventory
    for out in recipe['O']:
        name, quant = out
        addout = quant * multiplier
        inventory[name] += addout
        if DEBUG:
            printIng(addout, name)

    return inventory


def getRecipes(
        inventory,
        input_lookup,
        inputs_per_recipe,
        recipe_ages,
        curr_age
    ):
    possible_recipes = Counter()
    for ing, quant in inventory.items():
        if quant > 0.1:
            possible_recipes.update(input_lookup[ing])
    valid_recipes = [
        recid for recid, count in possible_recipes.items()
        if count == inputs_per_recipe[recid]
        and recipe_ages[recid] <= curr_age
    ]
    return valid_recipes


def main(configdict):
    # my_farms = [
    #     ['fir wood lumber axe farm', 1],
    #     ['railcraft water tank', 3]
    # ]
    # starting_resource = 'wood'

    # with open('data/farms.json', 'r') as f:
    #     available_farms = json.load(f)
    # farm_lookup = {x['name']: i for i, x in enumerate(available_farms)}

    # resources_per_10s = defaultdict(float)
    # for farm in my_farms:
    #     data = available_farms[farm_lookup[farm[0]]]
    #     production_time = [x for x in data['I'] if 'time (s)' in x[0]]
    #     if not production_time:
    #         raise RuntimeError(f'Please input production time for {farm["name"]}.')
    #     else:
    #         time_multiplier = 10 / production_time[0][1]

    #     for output in data['O']:
    #         resources_per_10s[output[0]] += output[1]*time_multiplier*farm[1]

    # TODO: Add cycle detection (track all seen input/output combos)

    ages = ['S', 'LV', 'MV', 'HV', 'EV', 'IV', 'LuV', 'ZPM', 'UV', 'UHV']

    t = configdict['optimal_target']
    banned_machines = set(configdict['banned_machines'])
    if t == 'EU':
        optimal_condition = lambda inventory: inventory['EU']
    elif t == 'EU/t':
        optimal_condition = lambda inventory: inventory['EU'] / (inventory['time']*20)
    elif t == 'hydrogen':
        optimal_condition = lambda inventory: inventory['fluid - hydrogen gas']
    elif t == 'oxygen':
        optimal_condition = lambda inventory: inventory['fluid - oxygen gas']
    elif t == 'oxygen/t':
        optimal_condition = lambda inventory: inventory['fluid - oxygen gas'] / (inventory['time']*20)
    elif t == 'nitrogen':
        optimal_condition = lambda inventory: inventory['fluid - nitrogen gas']
    else:
        raise RuntimeError(f'Unsupported optimization target: {t}')

    DEBUG = configdict['DEBUG']
    if DEBUG:
        DEBUG = 2

    ages = {x: i for i, x in enumerate(ages)}
    curr_age = ages[configdict['processing_level']]

    inventory = defaultdict(float, configdict['inventory'])
    start_inventory = inventory

    recipes, input_lookup, output_lookup = loadRecipesAndTables(
        'data/powergen_recipes.json',
        configdict['processing_level']
    )
    inputs_per_recipe = {i: len(x['I']) for i, x in enumerate(recipes)}
    recipe_ages = {i: ages[x['ma']] for i, x in enumerate(recipes)}

    optimal = {
        'score': 0,
        'id': 0
    }

    q = deque()
    # Now look up possible paths forward
    valid_recipes = getRecipes(
        inventory,
        # Reference material
        input_lookup,
        inputs_per_recipe,
        recipe_ages,
        curr_age
    )

    # Seed initial recipes
    for rec in valid_recipes:
        q.append((
            rec,
            0
        ))

    start = time.time()
    view_count = Counter()

    inventory_states = {
        0: start_inventory
    }
    machine_processing_routes = {
        0: []
    }
    top_state = 1

    timeout = False
    while q:
        recipe_index, parent_id = q.pop()
        recipe = recipes[recipe_index]
        # if recipe_index in machine_processing_routes[parent_id]:
        #     # TODO: Handle this in a less duct-taped way
        #     continue
        parent_inventory = inventory_states[parent_id]
        if recipe['m'] in banned_machines:
            continue
        inventory = deepcopy(parent_inventory)
        machine_processing_routes[top_state] = [parent_id, recipe_index]

        view_count[recipe_index] += 1

        # Subtract inputs, add outputs
        inventory = updateInventory(
            inventory,
            recipe,
            recipe_index,
            DEBUG=DEBUG
        )
        inventory_states[top_state] = inventory
        score = optimal_condition(inventory)
        if score > optimal['score']:
            optimal['score'] = score
            optimal['id'] = top_state

        # Now get valid paths
        valid_recipes = getRecipes(
            inventory,
            input_lookup,
            inputs_per_recipe,
            recipe_ages,
            curr_age,
        )

        # Append to q
        for rec in valid_recipes:
            q.append((
                rec,
                top_state
            ))

        top_state += 1

        if DEBUG:
            print('------')
            input()

        if time.time() - start > configdict['max_program_runtime']:
            timeout = True
            break

    blacklisted_terms = {}
    def print_inventory(inventory, indent=1):
        for ing, quant in inventory.items():
            if ing not in blacklisted_terms:
                if quant > 0.0001 or quant < -0.0001:
                    if indent > 1:
                        print(' '*(indent-1), ing, quant)
                    else:
                        print(ing, quant)

    age = configdict['processing_level']
    optimal_target = configdict['optimal_target']
    cprint(f'Best possible score/input ({age}): ', 'green', end='')
    print(f'{round(optimal["score"], 0)} ({optimal_target})')

    print()
    cprint('Starting inventory:', 'green')
    print_inventory(start_inventory, indent=4)

    print()
    cprint('Processing chain:', 'green')

    # Backtrack processing chain
    curr_id = optimal['id']
    processing_chain = []
    while curr_id != 0:
        curr_id, recipe = machine_processing_routes[curr_id]
        processing_chain.append(recipe)

    # TODO: Merge overlapping recipes
    inventory = start_inventory
    for rec in processing_chain[::-1]:
        # Retrace steps for end user
        recipe = recipes[rec]
        inventory = updateInventory(
            inventory,
            recipe,
            rec,
            DEBUG=True
        )

    print()
    cprint('Final inventory:', 'green')
    print_inventory(inventory, indent=4)
    # Compute amoritized cost
    # For single machine, take longest machine time, then add EU/t multiplying by
    #     current machine time / max machine time.
    # For parallel/pipelined, take shortest machine time, then add EU/t multiplying by
    #     current machine time / min machine time.
    processing_recipes = [recipes[rec] for rec in processing_chain]
    nonzero_dur = [r for r in processing_recipes if abs(r['dur']) > 0.01]

    dur_index = lambda x: x['dur']
    shortest = min(nonzero_dur, key=dur_index)['dur']
    longest = max(nonzero_dur, key=dur_index)['dur']

    single_amoritized, parallel_amoritized = 0, 0
    for recipe in processing_recipes:
        single_amoritized += recipe['eut'] * (recipe['dur'] / longest)
        parallel_amoritized += recipe['eut'] * (recipe['dur'] / shortest)

    for r in processing_recipes:
        print(r)
    print('   ', f'Amoritized cost (single machines {longest}s): {round(single_amoritized, 2)} EU/t')
    print('   ', f'Amoritized cost (in parallel {shortest}s): {round(parallel_amoritized, 2)} EU/t')

    print()
    cprint('Most viewed recipes:', 'green')
    for k, v in view_count.most_common(10):
        print(k, v)
    print(f'Total: {sum(view_count.values())}')
    if timeout:
        cprint('Timed out.', 'red')



if __name__ == '__main__':
    #############################################
    configdict = {
        'processing_level': 'MV',
        'DEBUG': False,
        'inventory': {
            # 'EU': -455,
            'EU': 0,
            'time': 0,
            'fluid - water': 1_000_000,
            ### Power sources:
            # 'compost': 1,
            # 'wood': 1,
            # 'sugar beet': 1,
            # 'sapling': 1,
            # 'fluid - biomass': 1000,
            # 'fluid - nitrogen gas': 62.5, # -455 EU
            # 'fish': 1,

            ### Oxygen sources:
            # 'redstone': 1,
            # 'sugar cane': 1,
            # 'fireclay dust': 2,
            'cobblestone': 1,
            # 'sand': 9,
            # 'gravel': 1,
            # 'flint': 2,
            'fluid - oxygen gas': 2,
        },
        'max_program_runtime': 10,
        # Supported: EU, EU/t, hydrogen, oxygen, nitrogen
        'optimal_target': 'oxygen',
        'banned_recipes': [
        ],
        'banned_machines': [
            # 'burn time conversion',
            # 'pyrolyse oven (50% eff)'
        ]
    }
    #############################################

    main(configdict)