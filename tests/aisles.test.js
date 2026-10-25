const test = require('node:test');
const assert = require('node:assert');
const { aisleFor } = require('../js/aisles.js');

test('sorts lines into Trader Joe\'s sections', () => {
  const cases = {
    '2 garlic cloves, minced': 'Produce',
    '1 tablespoon minced fresh oregano (OR 1 teaspoon dried)': 'Produce',
    '3 sage leaves (chopped)': 'Produce',
    '2 teaspoons garlic powder': 'Spices & Baking',
    '1/4 teaspoon pepper': 'Spices & Baking',
    '1 red bell pepper, sliced': 'Produce',
    '1 cup heavy cream (or evaporated milk + 1 tsp cornstarch)': 'Dairy & Eggs',
    '2 cups chicken broth': 'Pasta, Grains & Canned',
    '1 (28-ounce) can diced tomatoes': 'Pasta, Grains & Canned',
    '1 tbsp fish sauce': 'Sauces, Oils & Condiments',
    '2 tablespoons olive oil': 'Sauces, Oils & Condiments',
    '1/2 cup crumbled feta cheese': 'Cheese',
    '2 cups cubed butternut squash': 'Produce',
    '1 tablespoon unsalted butter': 'Dairy & Eggs',
    '2 pounds boneless skinless chicken breast': 'Meat & Seafood',
    '12 oz fresh salmon, cubed': 'Meat & Seafood',
    '1 sheet puff pastry': 'Frozen',
    '1/4 cup raw pecans': 'Nuts, Seeds & Snacks',
    '1 teaspoon rice vinegar': 'Sauces, Oils & Condiments',
  };
  for (const [line, aisle] of Object.entries(cases)) assert.strictEqual(aisleFor(line), aisle, line);
});

test('leaves water off the list', () => {
  assert.strictEqual(aisleFor('1 cup water'), null);
  assert.strictEqual(aisleFor('water, (as needed)'), null);
  assert.notStrictEqual(aisleFor('1 cup watermelon'), null);
});
