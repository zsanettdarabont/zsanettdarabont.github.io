# Zsanett's Recipe Box

A static GitHub Pages site showing the recipes Zsanett cooks most: a grid of square photo cards, each opening a clean recipe page with just the ingredients and instructions.

## Add a recipe

1. Add the URL to `recipes.txt` (one per line).
2. Run the extractor (Python 3.9+, no dependencies):

   ```
   python3 scripts/extract_recipes.py
   ```

   It reads each page's schema.org Recipe data, keeps only the title, photo, ingredients and steps, saves the photo to `images/` and writes `data/recipes.json`. Pass URLs as arguments to update just those.
3. Commit and push. Pages redeploys in a minute or two.

Some sites (e.g. Half Baked Harvest) block scripts. For those, `pip install playwright` and the script opens the page in your Chrome automatically. Or save the page from your browser and run `python3 scripts/extract_recipes.py URL --html saved-page.html`.

To remove a recipe, delete its entry from `data/recipes.json` and its image.

## Preview locally

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Tests

```
python3 -m unittest discover -s tests
```
