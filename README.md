# Zsanett's Kitchen

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

The home page groups recipes into Chicken, Seafood, Beef, Vegetarian, Dessert and Breakfast. The script guesses the group from the dish name and ingredients; to move a recipe, change its `category` in `data/recipes.json` (re-running the script keeps your choice).

Instagram posts and reels work too: the script reads the recipe from the caption (bulleted ingredients and numbered steps) and uses the cover photo. This also needs Playwright.

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

**2. Build the shortcut** (Shortcuts app on the iPhone, iOS 17 or 18)

Shortcuts shows Apple's starter shortcuts and lots of "suggested" actions. Ignore all of them. You'll add each action by typing its exact name into the **Search Actions** bar at the bottom of the editor and tapping the matching result.

*Start a blank shortcut*

1. Open the **Shortcuts** app. In the bottom bar tap the **Shortcuts** tab (not Gallery or Automation).
2. Tap **+** in the top-right corner. A blank editor called **New Shortcut** opens, with suggestions and a **Search Actions** bar at the bottom.
3. Tap the **New Shortcut** title at the top → **Rename** → type `Add to Zsanett's Kitchen` → **Done** on the keyboard.

*Make it appear in the Share menu*

4. Tap the title again → **Details** (on iOS 17, tap the **ⓘ** button at the bottom instead). Turn on **Show in Share Sheet** → tap **Done**.
5. A grey block now sits at the top: "Receive **Images and 18 more** from **Share Sheet**". Tap the blue **Images and 18 more**, tap **Clear**, then tick only **URLs**, **Safari web pages** and **Text**. Tap **Done** (or tap outside the list).

*Action 1: pull the link out of what's shared*

6. Tap the **Search Actions** bar, type `Get URLs from Input`, and tap that result. The new block reads "Get URLs from **Shortcut Input**". Leave it as is.

*Action 2: send the link to GitHub*

7. Search `Get Contents of URL` and tap it. The block reads "Get contents of **URLs**", because Shortcuts automatically plugs in the previous step's output.
   - **Replace it:** tap the blue **URLs** token → **Clear Variable**. Then tap the empty URL field and paste:
     `https://api.github.com/repos/zsanettdarabont/zsanettdarabont.github.io/actions/workflows/add-recipe.yml/dispatches`
8. Tap **Show More** (or the **›** arrow) on that block to open its options:
   - **Method:** tap **GET** → choose **POST**.
   - **Headers:** tap **Add new header**. In **Key** type `Authorization`. In **Text** type `Bearer `, then one space, then paste your token.
   - Tap **Add new header** again. **Key:** `Accept`, **Text:** `application/vnd.github+json`.
   - **Request Body:** leave it on **JSON**.
   - Tap **Add new field** → **Text**. **Key:** `ref`, **Text:** `main`.
   - Tap **Add new field** → **Dictionary**. **Key:** `inputs`. Tap its value (it says "0 items"), tap **Add new field** → **Text**, and set **Key** to `url`. Tap the empty **Text** box. In the bar just above the keyboard, tap the **URLs** variable, which comes from step 6. A blue **URLs** token should appear. Tap **Done** to close the dictionary.

*Action 3: confirmation*

9. Search `Show Notification` and tap it. Tap the placeholder text (e.g. "Hello World!"), delete it, and type `Sent to Zsanett's Kitchen. It'll be on the site in ~3 minutes.`
10. Tap **Done** in the top-right corner. The shortcut is saved.

When you're done, the editor shows the grey **Receive** block plus 3 actions in this order: **Get URLs from Input** → **Get Contents of URL** → **Show Notification**.

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

## This week's menu

Tap **+** on a recipe card, or **Add to this week's menu** on a recipe page, then open **This week's menu**. It shows a shopping list sorted into Trader Joe's-style sections (`js/aisles.js`), with items you can tick off. The menu and ticks are saved in that browser only. JS tests: `node --test tests/aisles.test.js`.
