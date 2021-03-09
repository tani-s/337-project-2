import json
from bs4 import BeautifulSoup
import requests
from unicodedata import numeric
import nltk
import re
#from pattern.en import pluralize
import veggies
import pprint
import ingPy
from helper import get_after_prefix, apply, get_POS_after_prefix



url = 'https://www.allrecipes.com/recipe/273864/greek-chicken-skewers/'

url2 = 'https://www.allrecipes.com/recipe/228122/herbed-scalloped-potatoes-and-onions/'


# incomplete, but a start
# liters, gallons, oz, fl oz, bottle, abbreviations of the above, pint, mL, quarts, 
# clove, dash, pinch, cube, can, kg, strip, piece, slice, packet, package, head, bunch
nouns = ["NN","NNP","NNS"]
adj = ["JJ","JJR","JJS","DT"]

tools = {"cut": "knife",
        "chop": "knife",
        "slice": "knife",
        "mince": "knife",
        "whisk": "whisk",  # "whisk with a fork" is a possibility...
        "grate": "grater",
        "stir": "spoon"}

tool_phrases = ["using a", "use a", "with a", "in a", "in the"]
tool_phrases = apply(nltk.word_tokenize, tool_phrases)

tool_phrases2 = ["using", "use", "with", "in"]
tool_phrases2 = apply(nltk.word_tokenize, tool_phrases2)

methods = ["bake", "fry", "sear", "saute", "boil", "braise", "poach"]

tools_2 = ["oven", "baking sheet", "baking dish", "pan", "saucepan", "skillet", "pot",
        "spatula", "fork", "foil", "knife", "whisk", "grater", "spoon"]

time_measure = ["second", "minute", "hour", "seconds", "minutes", "hours"]

health_sub = {"butter": "coconut oil",
        "sugar": "zero calorie sweetener",
        "lard": "coconut oil",
    "flour": "whole wheat flour",
"noodles": "whole grain pasta",
"spaghetti": "whole grain pasta",
"linguini": "whole grain pasta",
"penne": "whole grain pasta",
"bread": "whole wheat bread"
}


Lithuanian_sub = {"vegetable oil": "flaxseed oil", "coconut oil": "flaxseed oil", "olive oil": "flaxseed oil",
     "hot dog": "skilandis", "bratwurst": "skilandis", "salami": "skilandis",
     "beer": "farmhouse brewed beer", "wine": "fruit wine","coffee": "kava",
     "goose": "chicken", "mutton": "lamb", "veal": "lamb", "rabbit": "lamb",
     "walleye": "zander", "cod": "perch", "tuna": "pike",
     "basil": "bay leaf", "rosemary": "caraway", "thyme": "coriander" ,"parsley": "horseradish", 
     "wheat bread": "rye bread", "bagel": "rye bread", "biscuit": "rye bread", "brioche": "rye bread",
     "ciabatta":"rye bread", "naan": "rye bread","pita": "rye bread", "sourdough bread": "rye bread", "french bread": "rye bread",
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
    
    tool1=set()
    for step in instructions:
        for word in step['text'].lower().split():
            if word in tools:
                tool1.add(tools[word])
    
    for step in instructions:
        sent = step['text'].lower()
        words = nltk.word_tokenize(sent)
        for word in words:
            if word in tools:
                tool.add(tools[word])
        pos = nltk.pos_tag(words)
        1+1
        #post_phrases = get_after_prefix(words, tool_phrases)
        post_phrases = get_POS_after_prefix(pos, tool_phrases2, adj, ignore=True)
        for pp in post_phrases:
            tool.add(pp)
            
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
        temp = -1
        for i in split:
            if "VB" in i[1] and temp == -1:
                index = len(methods)
                main_method = i[0]
            if i[0] in methods:
                temp = methods.index(i[0])
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
            if 1 < ing[key][0] <= 2:  # plurals need changing
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
            else: 
                ing[key][0] /= 2
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
def url_to_transform(url, transform):
    ing, steps = transform(url)
    
    recipe = {
        'name': get_recipe_name(url),
        'ingredients': ing,
        'tools': get_tools(url),
        'method': get_method(url),
        'steps': steps,
    }
    return recipe

def url_to_transform_gen(url, third):
    ing, steps = transform(url, third)
    
    recipe = {
        'name': get_recipe_name(url),
        'ingredients': ing,
        'tools': get_tools(url),
        'method': get_method(url),
        'steps': steps,
    }
    return recipe

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

def printStep(steps):
    for i in range(1, len(steps) + 1):
        print ("step number " + str(i))
        temp = ", "
        temp = temp.join(steps[i][0])
        print("     actions: " + temp)
        if len(steps[i][1]) > 0:
            temp = ", "
            temp = temp.join(steps[i][1])
            print("     ingredients: " + temp)
        else:
            print("     no ingredients")
        if len(steps[i][2]) > 0:
            temp = ", "
            temp = temp.join(steps[i][2])
            print("     tools: " + temp)
        else:
            print("     no tools")
        if len(steps[i][3]) > 0:
            temp = ", "
            temp = temp.join(steps[i][3])
            print("     time: " + temp)
        else:
            print("     no time")

def printCount(steps):
    for i in range(1, len(steps) + 1):
        print("     " + str(i) + ": " + steps[i - 1])

def main():
    url = input("Enter a URL to parse!\n")
    while "allrecipes" not in url:
        url = input("URL invalid (must be allrecipes). Try again:")
    function = input('''What would you like to do? \n 
    [a] Parse as-is
    [b] Transform to vegetarian 
    [c] Parse with recipe doubled
    [d] Parse with recipe halved
    [e] Transform to Lithuanian
    [f] Transform to healthy
    ''')
    if function == 'a' or function == 'A':
        recipe = url_to_recipe(url)
        print('Recipe name: ' + recipe['name'])
        ingPy.ing_print(recipe['ingredients'])
        print('Tools: %s' %recipe['tools'])
        print('Primary method: %s' %recipe['method'])
        print('Steps: ')
        printStep(recipe['steps'])
    elif function == 'b' or function == 'B':
        recipe = url_to_transform(url, veg_transform)
        print('Recipe name: ' + recipe['name'])
        ingPy.ing_print(recipe['ingredients'])
        print('Tools: %s' %recipe['tools'])
        print('Primary method: %s' %recipe['method'])
        print('Steps: ')
        printCount(recipe['steps'])
    elif function == 'c' or function == 'C':
        recipe = double(url_to_recipe(url))
        print('Recipe name: ' + recipe['name'])
        ingPy.ing_print(recipe['ingredients'])
        print('Tools: %s' %recipe['tools'])
        print('Primary method: %s' %recipe['method'])
        print('Steps: ')
        printStep(recipe['steps'])
    elif function == 'd' or function == 'D':
        recipe = halve(url_to_recipe(url))
        print('Recipe name: ' + recipe['name'])
        ingPy.ing_print(recipe['ingredients'])
        print('Tools: %s' %recipe['tools'])
        print('Primary method: %s' %recipe['method'])
        print('Steps: ')
        printStep(recipe['steps'])
    elif function == 'e' or function == 'E':
        recipe = url_to_transform_gen(url, Lithuanian_sub)
        print('Recipe name: ' + recipe['name'])
        ingPy.ing_print(recipe['ingredients'])
        print('Tools: %s' %recipe['tools'])
        print('Primary method: %s' %recipe['method'])
        print('Steps: ')
        printCount(recipe['steps'])
    elif function == 'f' or function == 'F':
        recipe = url_to_transform_gen(url, health_sub)
        print('Recipe name: ' + recipe['name'])
        ingPy.ing_print(recipe['ingredients'])
        print('Tools: %s' %recipe['tools'])
        print('Primary method: %s' %recipe['method'])
        print('Steps: ')
        printCount(recipe['steps'])
main()
url3 = 'https://www.allrecipes.com/recipe/166583/spicy-chipotle-turkey-burgers/?internalSource=hub%20recipe&referringContentType=Search'
#print(double(url_to_recipe(url2)))
#print(halve(url_to_recipe(url2)))


