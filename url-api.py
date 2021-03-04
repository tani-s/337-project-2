import json
from bs4 import BeautifulSoup
import requests
from unicodedata import numeric
import nltk


url = 'https://www.allrecipes.com/recipe/273864/greek-chicken-skewers/'

url2 = 'https://www.allrecipes.com/recipe/228122/herbed-scalloped-potatoes-and-onions/'

measure = ['cup', 'tablespoon', 'teaspoon', 'gram', 'pound',
        'cups', 'tablespoons', 'teaspoons', 'grams', 'pounds']
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

time_measure = ["second", "seconds", "minute", "minutes", "hour", "hours"]
health_sub = {"butter": "olive oil",
        "sugar": "zero calorie sweetener",
        "lard": "olive oil"}


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


# given a URL, returns a dictionary of ingredients that maps to a list containing
#   the amount (in index 0) and the measure (index 1).
def get_ingredients(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    ingredients = j[1]['recipeIngredient']

    ing_dict = {}
    for ing in ingredients:
        lst = parse_ingredients(ing)
        ing_dict[lst[2]] = [lst[0], lst[1]]

    return ing_dict


# helper function for get_ingredients.
def parse_ingredients(ing):
    #amount, measurement, description
    amt = None
    mes = None
    desc = ing.split()

    info = ing.split()


    if fraction_handler(info[0]):
        amt = fraction_handler(info[0])

        if fraction_handler(info[1]):  # mixed fractions will be separated by a space
            amt += fraction_handler(info[1])
            desc.remove(info[1])

        desc.remove(info[0])

    if desc[0] in measure:
        mes = desc[0]
        desc.remove(desc[0])

    desc = ' '.join(desc)
    return [amt, mes, desc]
#print(get_ingredients(url))


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

# returns the given steps of the recipe, as laid out on the web page
# could be split into more steps, by looking for imperatives? each imperative verb starts a new step?
def get_steps(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']
    ingredients = get_ingredients(url)
    #print(ingredients)
    tools = get_tools(url)
    #print(tools)

    # dict of steps, key is step number, value is [method, ingredients, tools, time]
    # i want to split each step into chunks starting with the verbs
    steps = {}
    step_num = 0
    for step in instructions:
        sents = nltk.sent_tokenize(step['text'].lower().strip())
        for sent in sents:
            step_num += 1
            words = nltk.word_tokenize(sent)
            words = nltk.pos_tag(words)
            # bc first word is always the action verb
            method = [words[0][0]]
            ingred = []
            tools = []
            time = None
            for word in words:
                if word[1] == 'VB':
                    method.append(word[0]) 
                if word[0] in time_measure:
                    # how to get the word before the time??
                    time = word[0]           
                if word[1] == 'NN':
                    if word[0] in tools:
                        tools.append(word[0])
                    else: ingred.append(word[0])
            steps[step_num] = [method, ingred, tools, time]
    return steps

#print(get_steps(url))

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
        lst = parse_ingredients(ing)
        ing_dict[health_sub_help(lst[2])] = [lst[0], lst[1]]

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
                ing[key][1] += 's'
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
        'ingredients': get_ingredients(url),
        'tools': get_tools(url),
        'method': get_method(url),
        'steps': get_steps(url),
    }
    return recipe

#print(get_ingredients(url2))
#print(get_tools(url2))
#print(get_steps(url2))
#print(get_method(url2))
#print(healthify(url2))
print(halve(url_to_recipe(url2))['ingredients'])

# print(url_to_recipe(url2))
