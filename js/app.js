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

  async function renderGrid() {
    const grid = document.getElementById('grid');
    const search = document.getElementById('search');
    const recipes = await load();

    const draw = query => {
      const q = query.trim().toLowerCase();
      const shown = recipes.filter(r =>
        !q || r.name.toLowerCase().includes(q) ||
        r.ingredients.some(i => i.toLowerCase().includes(q)));
      grid.replaceChildren(...shown.map(r =>
        el('li', { class: 'card' },
          el('a', { href: `recipe.html?r=${encodeURIComponent(r.id)}` },
            el('div', { class: 'thumb' },
              r.image ? el('img', { src: r.image, alt: r.name, loading: 'lazy' }) : ''),
            el('div', { class: 'card-body' },
              el('h2', {}, r.name),
              el('span', { class: 'source' }, domain(r.source)))))));
      if (!shown.length) grid.append(el('li', { class: 'empty' }, 'No recipes match.'));
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
    document.title = `${r.name} · Zsanett's Recipe Box`;

    const ingredients = el('ul', { class: 'ingredients' }, ...r.ingredients.map((text, i) =>
      el('li', {}, el('label', {}, el('input', { type: 'checkbox', id: `ing-${i}` }), el('span', {}, text)))));

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
