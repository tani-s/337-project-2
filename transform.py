import json
from bs4 import BeautifulSoup
import requests
import nltk

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
        lst = parse_ingredients(ing)
        ing_dict[transform_help(lst[2], food_sub)] = [lst[0], lst[1]]

    steps = []
    for step in instructions:
        steps.append(transform_help(step['text'].lower().strip(), food_sub))
    return ing_dict, steps

def transform_help(step, food_sub):
    next = step
    for i in food_sub:
        next = next.replace(i, food_sub[i])
    return next
