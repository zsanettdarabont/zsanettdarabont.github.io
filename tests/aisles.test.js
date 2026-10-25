const test = require('node:test');
const assert = require('node:assert');
const { aisleFor, itemName, shoppingList } = require('../js/aisles.js');

test('sorts lines into Trader Joe\'s sections', () => {
  const cases = {
    '2 garlic cloves, minced': 'Produce',
    '1 tablespoon minced fresh oregano (OR 1 teaspoon dried)': 'Produce',
    '1 red bell pepper, sliced': 'Produce',
    '2 honeycrisp apples, thinly sliced': 'Produce',
    '2 teaspoons garlic powder': 'Spices',
    '1/2 teaspoon red pepper flakes': 'Spices',
    '1 cup heavy cream (or evaporated milk + 1 tsp cornstarch)': 'Dairy & Eggs',
    '2 cups chicken broth': 'Pasta, Grains & Canned',
    '1 (28-ounce) can diced tomatoes': 'Pasta, Grains & Canned',
    '1 tbsp fish sauce': 'Sauces & Condiments',
    '1/2 cup crumbled feta cheese': 'Cheese',
    '2 cups cubed butternut squash': 'Produce',
    '2 pounds boneless skinless chicken breast': 'Meat & Seafood',
    '1 sheet puff pastry': 'Frozen',
    '8 flour tortillas': 'Bakery & Bread',
    '1 cup all-purpose flour': 'Baking',
  };
  for (const [line, aisle] of Object.entries(cases)) assert.strictEqual(aisleFor(line), aisle, line);
});

test('leaves off staples you already have', () => {
  for (const line of ['1 cup water', '2 tablespoons olive oil', '1/4 teaspoon pepper', 'kosher salt and black pepper', '1 teaspoon salt']) {
    assert.strictEqual(aisleFor(line), null, line);
  }
  assert.strictEqual(aisleFor('1 cup watermelon'), 'Other');
  assert.strictEqual(aisleFor('1/2 cup oil-packed sun-dried tomatoes'), 'Pasta, Grains & Canned');
});

test('keeps just the ingredient name', () => {
  const name = line => itemName(line, aisleFor(line));
  assert.strictEqual(name('4 garlic cloves, minced'), 'Garlic');
  assert.strictEqual(name('2 pounds boneless skinless chicken breast'), 'Chicken breast');
  assert.strictEqual(name('1/2 cup crumbled feta cheese'), 'Feta cheese');
  assert.strictEqual(name('6 cups arugula or shredded kale'), 'Arugula or kale');
  assert.strictEqual(name('2 tablespoons lemon juice'), 'Lemon');
  assert.strictEqual(name('1 (28-ounce) can diced tomatoes'), 'Diced tomatoes');
  assert.strictEqual(name('Freshly grated Parmesan cheese (for serving)'), 'Parmesan cheese');
});

test('merges repeats and folds spices into one line', () => {
  const recipes = [
    { name: 'A', ingredients: [{ items: ['2 cloves garlic', '1 tsp ground cumin', '1 tsp salt', '1 tbsp olive oil'] }] },
    { name: 'B', ingredients: [{ items: ['3 garlic cloves, minced', '1 tsp EACH salt, garlic powder, cumin'] }] },
  ];
  assert.deepStrictEqual(shoppingList(recipes).map(([aisle, list]) => [aisle, list.map(x => [x.name, x.from])]), [
    ['Produce', [['Garlic', ['A', 'B']]]],
    ['Spices', [['Spices: cumin, garlic powder', ['A', 'B']]]],
  ]);
});
