import json
from bs4 import BeautifulSoup
import requests

url = 'https://www.allrecipes.com/recipe/273864/greek-chicken-skewers/'


def get_recipe_name(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    recipe_name = soup.find("h1", class_="headline heading-content").text
    return recipe_name

def get_ingredients(url):
    ingredients = []
    

print(get_recipe_name(url))