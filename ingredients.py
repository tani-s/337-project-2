import json
from bs4 import BeautifulSoup
import requests
from unicodedata import numeric
import nltk
import re
from pattern.en import pluralize
import veggies
# Ingredient getter + parser

# an ing_dict is a dict of ingredients
# an ingredient is a list of information
# list element 0: quantity (int)
#              1: measurement (str)
#              2: name (str)
#              3: descriptor i.e. fresh, extra-virgin
#              4: preparation i.e. finely chopped
#              5: "as needed" (bool), whether quantity is "or as needed" in recipe
url = 'https://www.allrecipes.com/recipe/273864/greek-chicken-skewers/'

url2 = 'https://www.allrecipes.com/recipe/228122/herbed-scalloped-potatoes-and-onions/'
measure = ['cup', 'tablespoon', 'teaspoon', 'gram', 'pound',
        'cups', 'tablespoons', 'teaspoons', 'grams', 'pounds', 
        'liter', 'gallon', 'ounce', 'gal', 'oz', 'fl oz', 'fluid ounce', 'bottle', 'can',
        'liters', 'gallons', 'ounces', 'gals', 'ozs', 'fl ozs', 'fluid ounces', 'bottles', 'cans',
        'clove', 'dash', 'pinch', 'cube', 'kilogram', 'kg', 'strip', 'piece', 'slice', 'packet', 'package', 'head', 'bunch',
        'cloves', 'dashes', 'pinches', 'cubes', 'kilograms', 'kgs', 'strips', 'pieces', 'slices', 'packets', 'packages', 'heads', 'bunches'
        ]
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

def get_ingredients(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    s = soup.find('script', type='application/ld+json')
    j = json.loads(s.string)
    ingredients = j[1]['recipeIngredient']

    ing_dict = {}
    for ing in ingredients:
        lst = parse_ingredients(ing)
        ing_dict[lst[2]] = [lst[0], lst[1], lst[3], lst[4], lst[5]]

    return ing_dict


# helper function for get_ingredients.
def parse_ingredients(ing):
    #amount, measurement, description, adjectives
    amt = None
    mes = None

    punct = '[,;!$%^&*]'
    name = re.sub(punct, "", ing).split()

    info = ing.split()

    desc = []
    prep = []
    as_needed = False


    # Get amounts
    if fraction_handler(info[0]) or fraction_handler(info[1]):
        amt = fraction_handler(info[0]) if fraction_handler(info[0]) else 0

        if fraction_handler(info[1]):  # mixed fractions will be separated by a space
            amt += fraction_handler(info[1])
            name.remove(info[1])

        name.remove(info[0])

    # Get as needed, and remove phrase from "name"
    if " as needed" in name or " or as needed" in ' '.join(name):
        if " or as needed" in ' '.join(name):
            name.remove("or")
        name.remove("as")
        name.remove("needed")
        as_needed = True

    # Get measurement
    if name[0] in measure:
        mes = name[0]
        name.remove(name[0])

    # Chunking rules 

    # phrases like "with a sharp knife" or "for about 30 minutes" will be part of preparation
    # this means: at least one preposition followed by 0 or more digits, followed by 0 or more determiners,
    #               followed by 0 or more adjectives, followed by 0 or more nouns of any kind
    patterns= """
    phrase:{<IN>+ <CD>* <DT>* <JJ>* <NN.*>*}
    preparation:{<RB>* <VB.*>}
    n:{<JJ|DT|CD>? <NN.*>+}
    descriptor:{<JJ.*>}
    """
    
    tagged_text = nltk.pos_tag(name)
    cp = nltk.RegexpParser(patterns) 
    #print(cp.parse(tagged_text))

    # 0 or more adverbs followed by a past tense verb (chopped, etc)
    # one adjective of any kind
    # optional determiner or digit followed by one or more nouns of any kind
    name = ''
    tree = cp.parse(tagged_text)
    #tree.draw()
    for chk in tree.subtrees():
        if chk.label() == 'n':
            name += ' '.join([x[0] for x in chk.leaves()])
        if chk.label() == 'preparation' or chk.label() == 'phrase':
            prep.append(' '.join([x[0] for x in chk.leaves()]))
        if chk.label() == 'descriptor':
            desc.append(' '.join([x[0] for x in chk.leaves()]))
    
    if name == '':  # name got categorized wrong; more likely it's under desc 
        name = ''.join(desc)
    
    return [amt, mes, name, desc, prep, as_needed]

print(get_ingredients(url))
print(get_ingredients(url2))