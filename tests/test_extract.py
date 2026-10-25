import sys
import unittest
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
        self.assertEqual(r["ingredients"], ["2 tomatoes", "1 cup basil"])
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


if __name__ == "__main__":
    unittest.main()
