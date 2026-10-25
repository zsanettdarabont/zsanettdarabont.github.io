// Sorts a shopping-list line into a Trader Joe's-style section. First matching rule wins.
const Aisles = (() => {
  const ORDER = [
    'Produce', 'Bakery & Bread', 'Meat & Seafood', 'Cheese', 'Dairy & Eggs', 'Frozen',
    'Pasta, Grains & Canned', 'Sauces, Oils & Condiments', 'Spices & Baking',
    'Nuts, Seeds & Snacks', 'Other',
  ];
  const HERBS = 'basil|oregano|thyme|sage|rosemary|parsley|cilantro|dill|mint|chives|ginger';
  const RULES = [
    ['Frozen', /\bfrozen\b|ice cream|puff pastry/],
    ['Produce', new RegExp(`\\bfresh(ly)?\\b.*\\b(${HERBS})`)],
    ['Pasta, Grains & Canned', /broth|stock|bouillon|tomato (paste|sauce|puree)|\bcans?\b|canned|crushed tomatoes|diced tomatoes|sun-dried|coconut milk|\bbeans\b|chickpeas|lentils|pasta|spaghetti|penne|rigatoni|linguine|fettuccine|orzo|noodles|\brice\b(?! vinegar)|quinoa|\boats\b|breadcrumbs|panko/],
    ['Spices & Baking', /powder|paprika|cumin|turmeric|garam masala|cinnamon|nutmeg|cloves? ground|ground (coriander|ginger|cloves)|coriander|seasoning|red pepper flakes|chili flakes|cayenne|dried (\w+ )?(oregano|basil|thyme|parsley|dill|rosemary)|herb blend|bay lea|peppercorns|(black|white|ground) pepper|salt and pepper|\bsalt\b|^[^a-z]*(teaspoons?|tsp|tablespoons?|tbsp)\b.*\bpepper\b|\bpepper\s*$|sugar|flour|baking soda|yeast|vanilla|chocolate|cocoa|cornstarch|extract|methi|fenugreek/],
    ['Sauces, Oils & Condiments', /\boils?\b|vinegar|soy sauce|tamari|fish sauce|oyster sauce|hoisin|sriracha|mustard|mayo|ketchup|honey|maple syrup|sambal|chili garlic sauce|chili crisp|liquid smoke|worcestershire|tahini|peanut butter|apple butter|pesto|salsa|\bwine\b|curry paste|gochujang|marinara|hot sauce|\bjam\b|dressing|croutons|olives|pickled|capers|\bamba\b/],
    ['Cheese', /cheese|parmesan|parmigiano|mozzarella|feta|ricotta|cheddar|pecorino|gruy[eè]re|cotija|burrata|halloumi/],
    ['Dairy & Eggs', /\bmilk\b|buttermilk|cream|\bbutter\b|yogh?urt|\beggs?\b|half[- ]and[- ]half|ghee|tofu|hummus|tzatziki/],
    ['Meat & Seafood', /chicken|beef|steak|pork|sausage|bacon|pancetta|prosciutto|\bham\b|turkey|lamb|salmon|shrimp|prawn|\bfish\b|\bcod\b|tuna|chuck|brisket|ground|thighs?\b|breasts?\b|veal/],
    ['Bakery & Bread', /bread|\bbuns?\b|tortillas?|pita|naan|baguette|\brolls?\b|brioche|ciabatta/],
    ['Nuts, Seeds & Snacks', /pecans|walnuts|almonds|cashews|peanuts|pumpkin seeds|pepitas|pistachios|sesame seeds|pine nuts|raisins|dried cranberries|\bdates\b|\bchips\b/],
    ['Produce', new RegExp(`onion|garlic|shallot|lemon|lime|orange|apple|tomato|potato|carrot|celery|zucchini|squash|peppers?\\b|jalape|chile|chilies|chilli|lettuce|romaine|arugula|kale|spinach|cabbage|cucumber|avocado|scallion|mushroom|broccoli|cauliflower|\\bpeas\\b|\\bcorn\\b|berr(y|ies)|pomegranate|banana|herbs|eggplant|sprouts|slaw|greens|radish|leek|fennel|${HERBS}`)],
  ];
  const SKIP = /^[\d\s\/.½¼¾⅓⅔⅛-]*(cups?|tablespoons?|tbsp|teaspoons?|tsp)?\s*(cold |warm |hot |boiling |ice )?(water|ice)\b/;

  function aisleFor(text) {
    const t = text.toLowerCase().replace(/\([^)]*\)/g, ' ').trim();
    if (SKIP.test(t)) return null;
    for (const [aisle, re] of RULES) if (re.test(t)) return aisle;
    return 'Other';
  }

  return { ORDER, aisleFor };
})();

if (typeof module !== 'undefined') module.exports = Aisles;
