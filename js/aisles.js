// Turns recipe ingredient lines into a shopping list grouped like a Trader Joe's.
const Aisles = (() => {
  const ORDER = [
    'Produce', 'Bakery & Bread', 'Meat & Seafood', 'Cheese', 'Dairy & Eggs', 'Frozen',
    'Pasta, Grains & Canned', 'Sauces & Condiments', 'Baking', 'Nuts, Seeds & Snacks',
    'Spices', 'Other',
  ];
  const HERBS = 'basil|oregano|thyme|sage|rosemary|parsley|cilantro|dill|mint|chives|ginger';
  const SPICE = /(garlic|onion|chili|chile|curry|ancho|chipotle|mustard|ginger) powder|paprika|cumin|turmeric|garam masala|cinnamon|nutmeg|allspice|cardamom|ground (coriander|ginger|cloves)|coriander|seasoning|red pepper flakes|chili flakes|cayenne|dried (\w+ )?(oregano|basil|thyme|parsley|dill|rosemary|chiles?)|herb blend|bay lea|peppercorns|methi|fenugreek|za'?atar|sumac/;
  // Things you'd already have at home.
  const STAPLE = /\bwater\b|\bice\b(?! cream)|\bsalt\b|(black|white|ground) pepper|\bpepper\s*$|^pepper\b|\boils?\b(?![- ]packed)|cooking spray/;
  const RULES = [
    ['Frozen', /\bfrozen\b|ice cream|puff pastry/],
    ['Produce', new RegExp(`\\bfresh(ly)?\\b.*\\b(${HERBS})`)],
    ['Pasta, Grains & Canned', /broth|stock|bouillon|tomato (paste|sauce|puree)|\bcans?\b|canned|crushed tomatoes|diced tomatoes|sun-dried|coconut milk|\bbeans\b|chickpeas|lentils|pasta|spaghetti|penne|rigatoni|linguine|fettuccine|orzo|noodles|\brice\b(?! vinegar)|quinoa|\boats\b|breadcrumbs|panko/],
    ['Baking', /sugar|flour\b(?! tortilla)|baking (soda|powder)|yeast|vanilla|chocolate|cocoa|cornstarch|extract/],
    ['Sauces & Condiments', /vinegar|soy sauce|tamari|fish sauce|oyster sauce|hoisin|sriracha|mustard|mayo|ketchup|\bhoney\b|maple syrup|sambal|chili garlic sauce|chili crisp|liquid smoke|worcestershire|tahini|peanut butter|apple butter|pesto|salsa|\bwine\b|curry paste|gochujang|marinara|hot sauce|\bjam\b|dressing|croutons|olives|pickled|capers|\bamba\b/],
    ['Cheese', /cheese|parmesan|parmigiano|mozzarella|feta|ricotta|cheddar|pecorino|gruy[eè]re|cotija|burrata|halloumi/],
    ['Dairy & Eggs', /\bmilk\b|buttermilk|cream|\bbutter\b|yogh?urt|\beggs?\b|half[- ]and[- ]half|ghee|tofu|hummus|tzatziki/],
    ['Meat & Seafood', /chicken|beef|steak|pork|sausage|bacon|pancetta|prosciutto|\bham\b|turkey|lamb|salmon|shrimp|prawn|\bfish\b|\bcod\b|tuna|chuck|brisket|ground|thighs?\b|breasts?\b|veal/],
    ['Bakery & Bread', /bread|\bbuns?\b|tortillas?|pita|naan|baguette|\brolls?\b|brioche|ciabatta/],
    ['Nuts, Seeds & Snacks', /pecans|walnuts|almonds|cashews|peanuts|pumpkin seeds|pepitas|pistachios|sesame seeds|pine nuts|raisins|dried cranberries|\bdates\b|\bchips\b/],
    ['Produce', new RegExp(`onion|garlic|shallot|lemon|lime|orange|apple|tomato|potato|carrot|celery|zucchini|squash|peppers?\\b|jalape|chile|chilies|chilli|lettuce|romaine|arugula|kale|spinach|cabbage|cucumber|avocado|scallion|mushroom|broccoli|cauliflower|\\bpeas\\b|\\bcorn\\b|berr(y|ies)|pomegranate|banana|herbs|eggplant|sprouts|slaw|greens|radish|leek|fennel|${HERBS}`)],
  ];

  const UNITS = 'cups?|c|tablespoons?|tbsps?|tbs|teaspoons?|tsps?|pounds?|lbs?|ounces?|oz|grams?|g|kg|ml|liters?|l|cloves?|pinch(?:es)?|dash(?:es)?|handfuls?|bunch(?:es)?|sprigs?|sheets?|cans?|jars?|packages?|pkgs?|slices?|sticks?|heads?|stalks?|large|medium|small|whole|inch(?:es)?|pieces?|each|quarts?|pints?|containers?|bags?|boxes?|ears?|fillets?|to|or|of|a|an|about|approximately|x|plain|good|quality|store-bought|homemade|recipe|minus|and|plus|[-&]';
  const LEAD = new RegExp(`^(?:[\\d\\s/.½¼¾⅓⅔⅛⅜⅝⅞–-]+|(?:${UNITS})\\b\\.?)\\s*`);
  const PREP = /\b(chopped|minced|diced|sliced|shredded|grated|crumbled|cubed|peeled|seeded|deseeded|cored|halved|quartered|softened|melted|room temperature|packed|loosely|lightly|thinly|finely|roughly|coarsely|freshly|julienned|trimmed|rinsed|drained|beaten|cooked|uncooked|divided|optional|torn|smashed|crushed|mashed|pitted|thawed|lean|boneless|skinless|raw|mild|ripe|large|medium|small|extra)\b/g;

  const tidy = line => line.toLowerCase()
    .replace(/\([^()]*\)|\{[^{}]*\}/g, ' ').replace(/\([^()]*\)/g, ' ').replace(/[*()]/g, ' ')
    .replace(/^[^:]{0,30}:\s*/, '').replace(/\s+/g, ' ').trim();

  function itemName(text, aisle) {
    let t = tidy(text)
      .replace(/\b(?:zest|juice|arils) (?:of|from) (?:half |\d+ )?(?:a |an )?(\w+)/, '$1')
      .replace(/\b(lemon|lime|orange) (?:juice|zest)\b/, '$1')
      .replace(/oil-packed/, '')
      .split(/,|\+|\s(?:for|from|to taste|plus|if|such as|like)\b/)[0];
    for (let prev; prev !== t;) { prev = t; t = t.replace(LEAD, ''); }
    const prep = aisle === 'Pasta, Grains & Canned' ? new RegExp(PREP.source.replace('diced|', '').replace('crushed|', ''), 'g') : PREP;
    t = t.replace(prep, ' ');
    if (/garlic/.test(t)) t = t.replace(/\bcloves?\b/, ' ');
    if (aisle === 'Produce') t = t.replace(/\b(fresh|leaves|ribs|matchsticks|squeezed|grilled)\b/g, ' ');
    if (aisle === 'Spices') t = t.replace(/\bground\b/, ' ');
    t = t.replace(/\s+/g, ' ').replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '').replace(/^(and|or|of) |\s(and|or|of)$/g, '').trim();
    return t && t[0].toUpperCase() + t.slice(1);
  }

  // Aisle for a whole line; null for staples, 'Spices' for spice lines.
  function aisleFor(text) {
    const t = tidy(text);
    if (SPICE.test(t)) return 'Spices';
    if (STAPLE.test(t)) return null;
    for (const [aisle, re] of RULES) if (re.test(t)) return aisle;
    return 'Other';
  }

  // recipes -> [[aisle, [{ key, name, from: [recipe names] }]]] in store order.
  function shoppingList(recipes) {
    const byAisle = {};
    const spices = new Map();
    const add = (aisle, name, from) => {
      if (!name) return;
      const key = name.toLowerCase().replace(/(es|s)\b/g, '');
      const list = (byAisle[aisle] ||= new Map());
      if (!list.has(key)) list.set(key, { key: `${aisle}|${key}`, name, from: [] });
      const item = list.get(key);
      if (!item.from.includes(from)) item.from.push(from);
    };
    for (const r of recipes) {
      for (const line of r.ingredients.flatMap(g => g.items)) {
        const aisle = aisleFor(line);
        if (aisle === 'Spices' || (aisle === null && SPICE.test(tidy(line)))) {
          for (const part of tidy(line).split(/,|\band\b|&/)) {
            if (!SPICE.test(part)) continue;
            const name = itemName(part, 'Spices').toLowerCase();
            const key = name.replace(/leaves\b/g, 'leaf').replace(/(es|s)\b/g, '');
            if (!spices.has(key)) spices.set(key, { name, from: r.name });
          }
        } else if (aisle) {
          add(aisle, itemName(line, aisle), r.name);
        }
      }
    }
    if (spices.size) {
      byAisle.Spices = new Map([['spices', {
        key: 'Spices|spices',
        name: `Spices: ${[...spices.values()].map(x => x.name).sort().join(', ')}`,
        from: [...new Set([...spices.values()].map(x => x.from))],
      }]]);
    }
    return ORDER.filter(a => byAisle[a]).map(a => [a, [...byAisle[a].values()]]);
  }

  return { ORDER, aisleFor, itemName, shoppingList };
})();

if (typeof module !== 'undefined') module.exports = Aisles;
