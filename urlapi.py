import json
from bs4 import BeautifulSoup
import requests
from unicodedata import numeric
import nltk
import re
from pattern.en import pluralize
import veggies
import pprint
import ingPy



url = 'https://www.allrecipes.com/recipe/273864/greek-chicken-skewers/'

url2 = 'https://www.allrecipes.com/recipe/228122/herbed-scalloped-potatoes-and-onions/'


# incomplete, but a start
# liters, gallons, oz, fl oz, bottle, abbreviations of the above, pint, mL, quarts, 
# clove, dash, pinch, cube, can, kg, strip, piece, slice, packet, package, head, bunch

tools = {"cut": "knife",
        "chop": "knife",
        "slice": "knife",
        "mince": "knife",
        "whisk": "whisk",  # "whisk with a fork" is a possibility...
        "grate": "grater",
        "stir": "spoon"}

methods = ["saute", "boil", "bake", "sear", "braise", "fry", "poach"]

tools_2 = ["oven", "baking sheet", "baking dish", "pan", "saucepan", "skillet", "pot",
        "spatula", "fork", "foil", "knife", "whisk", "grater", "spoon"]

time_measure = ["second", "minute", "hour", "seconds", "minutes", "hours"]

health_sub = {"butter": "olive oil",
        "sugar": "zero calorie sweetener",
        "lard": "olive oil"}


Lithuanian_sub = {"vegetable oil": "flaxseed oil", "coconut oil": "flaxseed oil", "olive oil": "flaxseed oil",
     "hot dog": "skilandis", "bratwurst": "skilandis", "salami": "skilandis",
     "beer": "farmhouse brewed beer", "wine": "fruit wine","coffee": "kava",
     "goose": "chicken", "mutton": "lamb", "veal": "lamb", "rabbit": "lamb",
     "walleye": "zander", "cod": "perch", "tuna": "pike",
     "basil": "bay leaf", "rosemary": "caraway", "thyme": "coriander" ,"parsley": "horseradish", 
     "wheat bread": "rye bread", "bagel": "rye bread", "biscuit": "rye bread", "brioche": "rye",
     "ciabatta":"rye", "naan": "rye bread","pita": "rye bread",
     "lemon": "apple", "orange": "apricot", "pineapple": "plum", "banana": "pear",
     "lettuce": "cabbage"}

dairy_free_sub = {"milk": "soy milk", "butter": "coconut oil", "cream": "coconut cream", 
    "parmesan": "nutritional yeast", "yogurt": "applesauce", "mayonnaise": "vegenaise", "cheese": "vegan cheese"}

# credit for this function to https://stackoverflow.com/questions/1263796/how-do-i-convert-unicode-characters-to-floats-in-python
# When given a fraction (or int), returns it as a float.
# When given a non-digit string, returns False.
# this will work for mixed numbers, like 3⅕ etc.
def fraction_handler(num):
    if len(num) == 1:
        v = numeric(num)
    elif num[-1].isdigit():
        # normal number, ending in [0-9]
        v = float(num)
    elif num == 'dozen':
        v = 12
    elif not num[-1].isdigit():
        # no digits.
        return False
    else:
        # Assume the last character is a vulgar fraction
        v = float(num[:-1]) + numeric(num[-1])
    return v


# given a URL, will return the name of the recipe
def get_recipe_name(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    recipe_name = soup.find("h1", class_="headline heading-content").text
    return recipe_name


# When given a url, returns a list of tools based on the tools dict defined at top
# We should probably add something to scan for ... Nouns? things like "oven", "pan", "plate", etc.
# Also for phrases like "With a spoon, xyz" or "use a spatula to xyz"
def get_tools(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']

    tool=set()  # so we don't get duplicates
    for step in instructions:
        for word in step['text'].lower().split():
            if word in tools:
                tool.add(tools[word])

    return tool

#print(get_tools(url))

# returns a dict of steps, key = step number, value = action, ingredients, tools, time
def get_steps(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']
    ingredients = ingPy.get_ingredients(url)

    # splitting into individual steps (by sentence, and splitting up ;s)
    steps = []
    for step in instructions:
        ss = nltk.sent_tokenize(step['text'].lower().strip())
        for s in ss:
            if ";" in s:
                split = s.split("; ")
                steps.append(split[0])
                steps.append(split[1])
            else: steps.append(s)

    instruc = {}
    step_num = 0
    for step in steps:
        ingred = []
        tools = []
        action = []
        time = []
        toks = nltk.word_tokenize(step)
        pos = nltk.pos_tag(toks)

        # getting ingredients from looking through ingredients list from get_ingredients
        # parsing through those ingredients bc usually they'll just say 'chicken' instead of 'skinless chicken breast' for example
        for i in ingredients:
            if i in step:
                ingred.append(i)
            tok = nltk.word_tokenize(i)
            tok = nltk.pos_tag(tok)
            for word in tok:
                if word[0] in step and (word[1] == "NN" or word[1] == "NNS"):
                    ingred.append(word[0])
        
        # getting tools, but from the list of commonly used tools at the top
        # could be altered to use get_tools
        for t in tools_2:
            if t in step:
                tools.append(t)
        
        # assuming first word is always an action verb, then also looking for other verbs
        action.append(pos[0][0])
        for word in pos:
            if word[1] == 'VB':
                action.append(word[0])
        
        # getting time...most steps dont have a time to it'll return an empty list for that
        for m in time_measure:
            if m in toks:
                #time = m
                index = toks.index(m)
                time.append(toks[index-1] + " " + toks[index])
                #time = index

        step_num += 1
        instruc[step_num] =  list(set(action)), list(set(ingred)), tools, time
    print("STEP NUMBER: ACTION, INGREDIENTS, TOOLS, TIME")
    return instruc

#pprint.pprint(get_steps(url2))
#pprint.pprint(get_steps(url))


def get_method(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']

    main_method = ""
    index = 12
    for step in instructions:
        split = nltk.word_tokenize(step['text'].lower().strip())
        split = nltk.pos_tag(split)
        for i in split:
            temp = -1
            if i[0] in methods:
                temp = methods.index(i[0])
            if "VB" in i[1] and temp != -1 and temp < index:
                index = temp
                main_method = i[0]
    return main_method

def healthify(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    ingredients = j[1]['recipeIngredient']

    ing_dict = {}
    for ing in ingredients:
        lst = ingPy.parse_ingredients(ing)
        ing_dict[health_sub_help(lst[2])] = [lst[0], lst[1], lst[3], lst[4], lst[5]]

    steps = []
    for step in instructions:
        steps.append(health_sub_help(step['text'].lower().strip()))
    return ing_dict, steps


def health_sub_help(step):
    next = step
    for i in health_sub:
        next = next.replace(i, health_sub[i])
    return next

def double(recipe): 
    ing = recipe['ingredients']
    for key in ing:
        if ing[key][0] is not None:
            if 0.5 < ing[key][0] <= 1 and ing[key][1] is not None:
                ing[key][1]= pluralize(ing[key][1])
                # make plural
            ing[key][0] *= 2
            #print(ing[key])

    doubled = {
        'name': recipe['name'],
        'ingredients': ing,
        'tools': recipe['tools'],
        'method': recipe['method'],
        'steps': recipe['steps'],
    }
    return doubled

def halve(recipe): 
    ing = recipe['ingredients']
    p = nltk.PorterStemmer()
    
    for key in ing.copy():
        if ing[key][0] is not None:
            if 1 < ing[key][0] <= 2:
                if ing[key][1] is not None:
                    ing_lst = ing[key][1].split()
                    i = 0
                    for word,pos in nltk.pos_tag(ing_lst):
                        #print(word, pos)
                        if pos == 'NNS':
                            ing_lst[i] = p.stem(word)
                        i += 1
                    ing[key][1] = ' '.join(ing_lst)
                    ing[key][0] /= 2
                
                else: # the plural that needs changing is in the desc, not the measure
                    ing_lst = key.split()
                    i = 0
                    for word,pos in nltk.pos_tag(ing_lst):
                        print(word, pos)
                        if pos == 'NNS':
                            ing_lst[i] = p.stem(word)
                        i += 1
                    
                    new_key = ' '.join(ing_lst)
                    new_val = ing[key]
                    del ing[key]
                    ing[new_key] = new_val
                    ing[new_key][0] /= 2
                    
                # could be chicken BREASTS or CLOVES garlic
                # de-pluralize
            
            #print(ing[key])

    halved = {
        'name': recipe['name'],
        'ingredients': ing,
        'tools': recipe['tools'],
        'method': recipe['method'],
        'steps': recipe['steps'],
    }
    return halved

def transform(url, food_sub):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    ingredients = j[1]['recipeIngredient']

    ing_dict = {}
    for ing in ingredients:
        lst = ingPy.parse_ingredients(ing)
        ing_dict[transform_help(lst[2], food_sub)] = [lst[0], lst[1], lst[3], lst[4], lst[5]]

    steps = []
    for step in instructions:
        steps.append(transform_help(step['text'].lower().strip(), food_sub))
    return ing_dict, steps

def transform_help(step, food_sub):
    next = step
    for i in food_sub:
        next = next.replace(i, food_sub[i])
    return next



# credit for this function to https://stackoverflow.com/questions/4664850/how-to-find-all-occurrences-of-a-substring
def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches

def url_to_recipe(url):
    recipe = {
        'name': get_recipe_name(url),
        'ingredients': ingPy.get_ingredients(url),
        'tools': get_tools(url),
        'method': get_method(url),
        'steps': get_steps(url),
    }
    return recipe

#print(ingredients.get_ingredients(url))
#print(ingredients.get_ingredients(url2))
#print(get_tools(url2))
#print(get_steps(url2))
#print(get_method(url2))
#print(healthify(url2))
#print(double(url_to_recipe(url2))['ingredients'])

# print(url_to_recipe(url2))

#print(transform(url, veggies.veg_sub))

#print(transform(url2, veggies.veg_sub))

#print(transform(url2, dairy_free_sub))


def veg_transform(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    ingredients = j[1]['recipeIngredient']

    ing_dict = {}
    for ing in ingredients:
        lst = ingPy.parse_ingredients(ing)
        ing_dict[veg_transform_help(lst[2])] = [lst[0], lst[1], lst[3], lst[4], lst[5]]

    steps = []
    for step in instructions:
        steps.append(veg_transform_help(step['text'].lower().strip()))
    return ing_dict, steps

def veg_transform_help(step):
    n = step
    for k in sorted(veggies.veg_sub, key= len, reverse=True):  # longest (more detailed) transforms first
        rep = r"\b" + k  # only make tranformations on words at the word boundary
        n = re.sub(rep, veggies.veg_sub[k], n)
    return n

#print(veg_transform(url))
#print(veg_transform(url2))




