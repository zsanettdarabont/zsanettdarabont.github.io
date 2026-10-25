const RecipeBox = (() => {
  const load = () => fetch('data/recipes.json').then(r => r.json());

  const el = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') node.className = v;
      else node.setAttribute(k, v);
    }
    node.append(...children);
    return node;
  };

  const domain = url => new URL(url).hostname.replace(/^www\./, '');
  const CATEGORIES = ['Chicken', 'Seafood', 'Beef', 'Vegetarian', 'Dessert', 'Breakfast'];
  const allIngredients = r => r.ingredients.flatMap(g => g.items);

  async function renderGrid() {
    const grid = document.getElementById('grid');
    const search = document.getElementById('search');
    const recipes = await load();

    const card = r =>
      el('li', { class: 'card' },
        el('a', { href: `recipe.html?r=${encodeURIComponent(r.id)}` },
          el('div', { class: 'thumb' },
            r.image ? el('img', { src: r.image, alt: r.name, loading: 'lazy' }) : ''),
          el('div', { class: 'card-body' },
            el('h3', {}, r.name),
            el('span', { class: 'source' }, domain(r.source)))));

    const draw = query => {
      const q = query.trim().toLowerCase();
      const shown = recipes.filter(r =>
        !q || r.name.toLowerCase().includes(q) ||
        allIngredients(r).some(i => i.toLowerCase().includes(q)));
      const groups = CATEGORIES.map(cat => [cat, shown.filter(r => r.category === cat)])
        .filter(([, list]) => list.length);
      grid.replaceChildren(...groups.map(([cat, list]) =>
        el('section', { class: 'group' },
          el('h2', { class: 'group-title' }, cat),
          el('ul', { class: 'grid' }, ...list.map(card)))));
      if (!shown.length) grid.append(el('p', { class: 'empty' }, 'No recipes match.'));
    };

    search.addEventListener('input', () => draw(search.value));
    draw('');
  }

  async function renderRecipe() {
    const root = document.getElementById('recipe');
    const id = new URLSearchParams(location.search).get('r');
    const r = (await load()).find(x => x.id === id);
    if (!r) {
      root.append(el('p', {}, 'Recipe not found. ', el('a', { href: './' }, 'Back to all recipes')));
      return;
    }
    document.title = `${r.name} · Zsanett's Kitchen`;

    let n = 0;
    const ingredients = el('div', { class: 'ingredient-groups' });
    for (const group of r.ingredients) {
      if (group.name) ingredients.append(el('h3', {}, group.name));
      ingredients.append(el('ul', { class: 'ingredients' }, ...group.items.map(text => {
        const id = `ing-${n++}`;
        return el('li', {}, el('label', {}, el('input', { type: 'checkbox', id }), el('span', {}, text)));
      })));
    }

    const method = el('div', { class: 'method' });
    for (const section of r.instructions) {
      if (section.name) method.append(el('h3', {}, section.name));
      method.append(el('ol', {}, ...section.steps.map(s => el('li', {}, s))));
    }

    const printBtn = el('button', { class: 'btn', type: 'button' }, 'Print recipe');
    printBtn.addEventListener('click', () => window.print());

    root.append(
      el('a', { class: 'back', href: './' }, '← All recipes'),
      el('article', { class: 'recipe-card' },
        el('div', { class: 'recipe-head' },
          r.image ? el('img', { class: 'hero', src: r.image, alt: r.name }) : '',
          el('div', { class: 'recipe-title' },
            el('h1', {}, r.name),
            el('p', { class: 'source' }, 'Recipe from ',
              el('a', { href: r.source, target: '_blank', rel: 'noopener' }, domain(r.source))),
            printBtn)),
        el('div', { class: 'recipe-body' },
          el('section', {}, el('h2', {}, 'Ingredients'), ingredients),
          el('section', {}, el('h2', {}, 'Instructions'), method))));
  }

  return { renderGrid, renderRecipe };
})();
