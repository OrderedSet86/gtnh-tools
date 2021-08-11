from core.utils import *

if __name__ == '__main__':
    recipes, inputLookup, outputLookup = loadRecipesAndTables('data/recipes.json', 'EV')

    user_recipes = []
    for r in recipes:
        for o in r['O']:
            if 'user' in o[0]:
                user_recipes.append(o[0])

    for l in user_recipes:
        print(l)