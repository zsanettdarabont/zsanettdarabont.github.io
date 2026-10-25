import gzip
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import extract_recipes as ex  # noqa: E402

PAGE = """
<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[
  {"@type":"WebPage","name":"Ignore me"},
  {"@type":["Recipe"],"name":"Tomato &amp; Basil Soup",
   "image":["https://example.com/soup-1200.jpg","https://example.com/soup-300.jpg"],
   "recipeIngredient":["2 <b>tomatoes</b>","1 cup  basil",""],
   "recipeInstructions":[
     {"@type":"HowToStep","text":"Chop the tomatoes."},
     {"@type":"HowToSection","name":"To serve","itemListElement":[
       {"@type":"HowToStep","text":"Ladle into bowls."}]}]}
]}</script>
</head><body><p>Long story about soup...</p></body></html>
"""


class ExtractTest(unittest.TestCase):
    def test_extracts_only_recipe_parts(self):
        r = ex.extract("https://example.com/soup", PAGE)
        self.assertEqual(r["name"], "Tomato & Basil Soup")
        self.assertEqual(r["id"], "tomato-basil-soup")
        self.assertEqual(r["image"], "https://example.com/soup-1200.jpg")
        self.assertEqual(r["ingredients"], [{"name": "", "items": ["2 tomatoes", "1 cup basil"]}])
        self.assertEqual(r["instructions"], [
            {"name": "", "steps": ["Chop the tomatoes."]},
            {"name": "To serve", "steps": ["Ladle into bowls."]},
        ])
        self.assertEqual(set(r), {"id", "name", "source", "image", "ingredients", "instructions"})

    def test_unquoted_script_type(self):
        page = PAGE.replace('type="application/ld+json"', "type=application/ld+json")
        self.assertEqual(ex.extract("https://example.com/soup", page)["name"], "Tomato & Basil Soup")

    def test_splits_numbered_steps_in_one_string(self):
        steps = ex.parse_steps("1. Preheat oven to 400° F.2. Toss the squash. 3.Bake 20 minutes.")
        self.assertEqual(steps[0]["steps"], ["Preheat oven to 400° F.", "Toss the squash.", "Bake 20 minutes."])

    def test_keeps_decimals(self):
        steps = ex.parse_steps("Add 1.5 cups water. Stir.")
        self.assertEqual(steps[0]["steps"], ["Add 1.5 cups water. Stir."])

    def test_tidies_doubled_parentheses(self):
        self.assertEqual(ex.clean("1/4 tsp cayenne ((optional))"), "1/4 tsp cayenne (optional)")
        self.assertEqual(ex.clean("1/2 tsp salt (adjust to taste))"), "1/2 tsp salt (adjust to taste)")
        self.assertEqual(ex.clean("1 carrot (diced (1 large))"), "1 carrot (diced (1 large))")

    def test_page_without_recipe(self):
        with self.assertRaises(ValueError):
            ex.extract("https://example.com", "<html><body>no recipe</body></html>")


    def test_unzips_gzip_pages(self):
        resp = mock.MagicMock()
        resp.__enter__.return_value = resp
        resp.read.return_value = gzip.compress(b"<html>hi</html>")
        resp.headers.get.return_value = "gzip"
        resp.headers.get_content_type.return_value = "text/html"
        with mock.patch.object(ex.urllib.request, "urlopen", return_value=resp):
            self.assertEqual(ex.fetch("https://example.com"), (b"<html>hi</html>", "text/html"))


    def test_recipe_from_instagram_caption(self):
        caption = (
            "cook_account\n\nPad Kra Pao 🔥\n\nComment \u201cRecipe\u201d for the card!\n"
            "For the sauce:\n-1 tbsp fish sauce\n* 1.5 tbsp palm sugar\n"
            "Instructions\n1. Mix the sauce.\n2. Fry and serve.\n#thaifood\nView all 577 comments"
        )
        r = ex.recipe_from_caption("https://www.instagram.com/p/X/", caption, "https://cdn/x.jpg")
        self.assertEqual(r["name"], "Pad Kra Pao")
        self.assertEqual(r["ingredients"], [
            {"name": "For the sauce", "items": ["1 tbsp fish sauce", "1.5 tbsp palm sugar"]}])
        self.assertEqual(r["instructions"], [{"name": "", "steps": ["Mix the sauce.", "Fry and serve."]}])
        self.assertEqual(r["image"], "https://cdn/x.jpg")

    def test_instagram_url_shapes(self):
        for u in ("https://www.instagram.com/p/C4dooVKp-Ax/", "https://www.instagram.com/reels/DLQKCZ1Pdmc/",
                  "https://www.instagram.com/reel/DT3iH2Ck7jQ/?igsh=x"):
            self.assertTrue(ex.INSTAGRAM.search(u))


    def test_wprm_ingredient_groups(self):
        page = (
            '<div class="wprm-recipe-ingredient-group"><ul><li class="wprm-recipe-ingredient">a</li>'
            '<li class="wprm-recipe-ingredient">b</li></ul></div>'
            '<div class="wprm-recipe-ingredient-group"><h4 class="wprm-recipe-group-name">Dressing:</h4>'
            '<ul><li class="wprm-recipe-ingredient">c</li></ul></div>'
            '<div class="wprm-recipe-instructions-container">'
        )
        self.assertEqual(ex.ingredient_groups(page, ["a", "b", "c"]), [
            {"name": "", "items": ["a", "b"]}, {"name": "Dressing", "items": ["c"]}])
        # Counts that don't line up fall back to one list.
        self.assertEqual(ex.ingredient_groups(page, ["a", "b"]), [{"name": "", "items": ["a", "b"]}])

    def test_guess_category(self):
        g = ex.guess_category
        self.assertEqual(g("Chicken Pot Pie", []), "Chicken")
        self.assertEqual(g("Best Chocolate Chip Cookies", ["2 eggs"]), "Dessert")
        self.assertEqual(g("Buttermilk Pancakes", []), "Breakfast")
        self.assertEqual(g("Pad Thai", ["1 lb shrimp", "2 tbsp fish sauce"]), "Seafood")
        self.assertEqual(g("Summer Pasta", ["1 cup chicken broth", "zucchini"]), "Vegetarian")
        self.assertEqual(g("Skillet Dinner", ["1 lb ground beef"]), "Beef")


    def test_wprm_card_without_schema(self):
        page = (
            '<div class="wprm-recipe-container"><h2 class="wprm-recipe-name">SAMIN\'S ROAST CHICKEN</h2>'
            '<div class="wprm-recipe-image"><img src="/s.jpg" srcset="/s.jpg 300w, /l.jpg 768w"></div>'
            '<div class="wprm-recipe-ingredient-group"><ul>'
            '<li class="wprm-recipe-ingredient"><span>2</span> <span>cups</span> <span>buttermilk</span></li>'
            '</ul></div><div class="wprm-recipe-instructions-container">'
            '<div class="wprm-recipe-instruction-group"><ol><li>'
            '<div class="wprm-recipe-instruction-text"><p>Marinate overnight.</p></div></li></ol></div>'
        )
        r = ex.extract("https://example.com/chicken", page)
        self.assertEqual(r["name"], "Samin's Roast Chicken")
        self.assertEqual(r["image"], "https://example.com/l.jpg")
        self.assertEqual(r["ingredients"], [{"name": "", "items": ["2 cups buttermilk"]}])
        self.assertEqual(r["instructions"], [{"name": "", "steps": ["Marinate overnight."]}])


if __name__ == "__main__":
    unittest.main()
