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

tools = {"cut": "knife",
        "chop": "knife",
        "slice": "knife",
        "mince": "knife",
        "whisk": "whisk",  # "whisk with a fork" is a possibility...
        "grate": "grater",
        "stir": "spoon"}

methods = ["saute", "boil", "bake", "sear", "braise", "fry", "poach"]


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
        desc.remove(info[0])
    if info[1] in measure:
        mes = info[1]
        desc.remove(info[1])

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

    tool=[]
    for step in instructions:
        for word in step['text'].lower().split():
            if word in tools:
                tool.append(tools[word])

    return tool

print(get_tools(url))

# returns the given steps of the recipe, as laid out on the web page
# could be split into more steps, by looking for imperatives? each imperative verb starts a new step?
def get_steps(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    instructions = j[1]['recipeInstructions']

    steps = []
    for step in instructions:
        steps.append(step['text'].lower().strip())
    return steps

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





print(get_ingredients(url2))
print(get_tools(url2))
print(get_steps(url2))
print(get_method(url2))
