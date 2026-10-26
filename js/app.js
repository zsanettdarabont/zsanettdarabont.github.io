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

  // The Shopping List recipes and ticks live in this browser only.
  const store = {
    get: (key, fallback) => {
      try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
    },
    set: (key, value) => localStorage.setItem(key, JSON.stringify(value)),
  };
  const menu = () => store.get('zk-menu', []);
  const updateMenuCount = () => {
    const count = document.getElementById('menu-count');
    if (count) count.textContent = menu().length || '';
  };
  const toggleMenu = id => {
    const m = menu();
    store.set('zk-menu', m.includes(id) ? m.filter(x => x !== id) : [...m, id]);
    updateMenuCount();
  };

  const menuButton = (r, compact) => {
    const btn = el('button', { class: compact ? 'add-btn' : 'btn btn-menu', type: 'button' });
    const sync = () => {
      const on = menu().includes(r.id);
      btn.textContent = compact ? (on ? '✓' : '+') : (on ? '✓ On Shopping List' : '+ Add to Shopping List');
      btn.classList.toggle('on', on);
      btn.setAttribute('aria-pressed', on);
      btn.setAttribute('aria-label', on ? `Remove ${r.name} from Shopping List` : `Add ${r.name} to Shopping List`);
    };
    btn.addEventListener('click', e => { e.preventDefault(); toggleMenu(r.id); sync(); });
    sync();
    return btn;
  };

  async function renderGrid() {
    const grid = document.getElementById('grid');
    const search = document.getElementById('search');
    const recipes = await load();
    updateMenuCount();

    const card = r =>
      el('li', { class: 'card' },
        el('a', { href: `recipe.html?r=${encodeURIComponent(r.id)}` },
          el('div', { class: 'thumb' },
            r.image ? el('img', { src: r.image, alt: r.name, loading: 'lazy' }) : ''),
          el('div', { class: 'card-body' },
            el('h3', {}, r.name),
            el('span', { class: 'source' }, domain(r.source)))),
        menuButton(r, true));

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
    updateMenuCount();
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
            el('div', { class: 'actions' }, menuButton(r, false), printBtn))),
        el('div', { class: 'recipe-body' },
          el('section', {}, el('h2', {}, 'Ingredients'), ingredients),
          el('section', {}, el('h2', {}, 'Instructions'), method))));
  }

  async function renderMenu() {
    const root = document.getElementById('menu');
    const recipes = await load();

    const draw = () => {
      updateMenuCount();
      const chosen = menu().map(id => recipes.find(r => r.id === id)).filter(Boolean);
      if (!chosen.length) {
        root.replaceChildren(
          el('h1', {}, 'Shopping List'),
          el('p', { class: 'empty' }, 'Nothing here yet. Tap + on any recipe to add it. ',
            el('a', { href: './' }, 'Browse recipes')));
        return;
      }

      const list = el('ul', { class: 'menu-list' }, ...chosen.map(r => {
        const remove = el('button', { class: 'remove', type: 'button', 'aria-label': `Remove ${r.name}` }, '×');
        remove.addEventListener('click', () => { toggleMenu(r.id); draw(); });
        return el('li', {},
          r.image ? el('img', { src: r.image, alt: '' }) : el('span', { class: 'menu-thumb' }),
          el('a', { href: `recipe.html?r=${encodeURIComponent(r.id)}` }, r.name),
          remove);
      }));

      const aisles = Aisles.shoppingList(chosen);
      const keys = new Set(aisles.flatMap(([, list]) => list.map(x => x.key)));
      const checked = new Set(store.get('zk-checked', []).filter(k => keys.has(k)));
      store.set('zk-checked', [...checked]);

      const shopping = el('div', { class: 'shopping' });
      for (const [aisle, list] of aisles) {
        shopping.append(el('h3', {}, aisle), el('ul', { class: 'ingredients' }, ...list.map(item => {
          const box = el('input', { type: 'checkbox' });
          box.checked = checked.has(item.key);
          box.addEventListener('change', () => {
            box.checked ? checked.add(item.key) : checked.delete(item.key);
            store.set('zk-checked', [...checked]);
          });
          return el('li', {}, el('label', {}, box,
            el('span', {}, item.name, el('small', { class: 'from' }, item.from.join(' · ')))));
        })));
      }

      const reset = el('button', { class: 'btn btn-light', type: 'button' }, 'Uncheck all');
      reset.addEventListener('click', () => { store.set('zk-checked', []); draw(); });

      root.replaceChildren(
        el('h1', {}, 'Shopping List'),
        list,
        el('div', { class: 'list-head' }, el('h2', {}, 'Groceries'), reset),
        shopping);
    };
    draw();
  }

  return { renderGrid, renderRecipe, renderMenu };
})();
