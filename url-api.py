import json
from bs4 import BeautifulSoup
import requests
from unicodedata import numeric


# credit to https://stackoverflow.com/questions/1263796/how-do-i-convert-unicode-characters-to-floats-in-python

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

url = 'https://www.allrecipes.com/recipe/273864/greek-chicken-skewers/'

measure = ['cup', 'tablespoon', 'teaspoon', 'gram', 'pound' ]
# will also need plurals

def get_recipe_name(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    recipe_name = soup.find("h1", class_="headline heading-content").text
    return recipe_name

# given a URL, returns a dictionary of ingredients that maps to a list containing
#   the amount in index 0 and the measure at index 1. 
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
    

print(get_ingredients(url))