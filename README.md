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

## Add a recipe from your iPhone

Share any recipe page to the **Add to Zsanett's Kitchen** shortcut. It starts the `Add recipe` GitHub Action (`.github/workflows/add-recipe.yml`), which extracts the recipe, commits it and redeploys the site. The recipe appears about 3 minutes later.

If a site blocks the Action, the link is still saved to `recipes.txt` and GitHub emails you that the run failed. Then run `python3 scripts/extract_recipes.py` on your Mac and push.

### One-time setup

**1. Create a GitHub token** (on a computer is easiest)

1. Signed in as **zsanettdarabont**, open https://github.com/settings/personal-access-tokens/new
2. **Token name:** `Zsanett's Kitchen shortcut`. **Expiration:** pick the longest you're comfortable with (you'll redo step 2.6 when it expires).
3. **Repository access:** *Only select repositories* → `zsanettdarabont/zsanettdarabont.github.io`.
4. **Permissions** → **Repository permissions** → **Actions:** *Read and write*. Leave everything else alone.
5. Click **Generate token** and copy it (it starts with `github_pat_`). Send it to your iPhone (e.g. AirDrop it, or paste it into a Note), because you'll paste it in step 2.6.

**2. Build the shortcut** (Shortcuts app on the iPhone)

1. Tap **+** to make a new shortcut. Tap its name at the top → **Rename** → `Add to Zsanett's Kitchen`.
2. Tap the **ⓘ** (or the name's dropdown → **Details**) and turn on **Show in Share Sheet**. Tap **Done**.
3. A "Receive **Images and 18 more** input from **Share Sheet**" block appears at the top. Tap **Images and 18 more**, choose **Clear**, then select only **URLs**, **Safari web pages** and **Text**.
4. Search the actions for **Get URLs from Input** and add it. It should say "Get URLs from **Shortcut Input**".
5. Add **Get Contents of URL**. Tap the **URL** placeholder and paste:
   `https://api.github.com/repos/zsanettdarabont/zsanettdarabont.github.io/actions/workflows/add-recipe.yml/dispatches`
6. Tap the **›** arrow on that block to expand it:
   - **Method:** `POST`
   - **Headers:** tap **Add new header** twice:
     - `Authorization` → `Bearer ` followed by your token (one space after Bearer)
     - `Accept` → `application/vnd.github+json`
   - **Request Body:** `JSON`, then **Add new field**:
     - **Text** field: key `ref`, value `main`
     - **Dictionary** field: key `inputs`. Inside it, add a **Text** field with key `url`. For the value, tap the box, choose **Select Variable**, and tap the **URLs** output from step 4.
7. Add **Show Notification**. Set the text to `Sent to Zsanett's Kitchen. It'll be on the site in ~3 minutes.`
8. Tap **Done**.

### Use it

On any recipe page (Safari, Chrome, Pinterest, Instagram…), tap **Share** → **Add to Zsanett's Kitchen**. The first time, iOS asks whether the shortcut may connect to api.github.com: tap **Always Allow**.

If nothing shows up after ~5 minutes, check https://github.com/zsanettdarabont/zsanettdarabont.github.io/actions for the run and its error.

## Preview locally

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Tests

```
python3 -m unittest discover -s tests
```
