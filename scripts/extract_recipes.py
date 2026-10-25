#!/usr/bin/env python3
"""Extract the recipe (title, photo, ingredients, steps) from recipe web pages.

Reads URLs from recipes.txt (or the command line), pulls the schema.org Recipe
data most recipe sites embed as JSON-LD, downloads the finished-dish photo to
images/, and writes everything to data/recipes.json for the website.

    python3 scripts/extract_recipes.py                  # every URL in recipes.txt
    python3 scripts/extract_recipes.py URL [URL ...]    # just these
    python3 scripts/extract_recipes.py URL --html page.html  # page saved from your browser
"""

import argparse
import gzip
import html
import json
import os
import re
import string
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "recipes.json"
IMAGE_DIR = ROOT / "images"
URL_LIST = ROOT / "recipes.txt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

LD_JSON = re.compile(
    r"<script[^>]*type=[\"']?application/ld\+json[\"']?[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
INSTAGRAM = re.compile(r"instagram\.com/(?:p|reels?|tv)/([\w-]+)")
TAG = re.compile(r"<[^>]+>")
# "1. Preheat oven.2. Toss..." -> split before each "N." that starts a sentence.
NUMBERED = re.compile(r"(?:^|(?<=[.!?)]))\s*\d{1,2}\.\s*(?=[A-Z])")


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":  # some sites send it unasked
            body = gzip.decompress(body)
        return body, resp.headers.get_content_type()


def fetch_page(url):
    try:
        return fetch(url)[0].decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 503):
            raise
    # Bot protection (e.g. Cloudflare): load the page in a real Chrome window.
    return in_chrome(url)


def in_chrome(url, script=None, wait_for=None):
    """Open url in a visible Chrome window; return the HTML, or the result of script."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "site blocks scripts; pip install playwright, or save the page "
            "from your browser and pass it with --html"
        ) from None
    with sync_playwright() as p:
        chrome = os.environ.get("CHROME_PATH")
        browser = p.chromium.launch(
            headless=False, **({"executable_path": chrome} if chrome else {"channel": "chrome"})
        )
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        for _ in range(30):
            if "Just a moment" not in page.title():
                break
            page.wait_for_timeout(1000)
        if wait_for:
            page.wait_for_selector(wait_for, timeout=30000)
        page.wait_for_timeout(1500)
        result = page.evaluate(script) if script else page.content()
        browser.close()
    return result


def clean(text):
    text = html.unescape(TAG.sub(" ", html.unescape(str(text))))
    text = re.sub(r"\s+", " ", text).strip()
    # Recipe plugins often wrap notes that already have parentheses: "((optional))".
    text = re.sub(r"\(\(([^()]*)\)\)", r"(\1)", text)
    while text.endswith(")") and text.count(")") > text.count("("):
        text = text[:-1].rstrip()
    return text


def find_recipe(node):
    """Depth-first search for a JSON-LD object whose @type includes Recipe."""
    if isinstance(node, list):
        for item in node:
            found = find_recipe(item)
            if found:
                return found
    elif isinstance(node, dict):
        types = node.get("@type", [])
        types = types if isinstance(types, list) else [types]
        if "Recipe" in types:
            return node
        for value in node.values():
            if isinstance(value, (list, dict)):
                found = find_recipe(value)
                if found:
                    return found
    return None


def recipe_from_html(page):
    for block in LD_JSON.findall(page):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        recipe = find_recipe(data)
        if recipe:
            return recipe
    return None


def recipe_from_wprm(page):
    """Read a WP Recipe Maker card straight from the HTML, for sites that turn off its schema data."""
    start = page.find('class="wprm-recipe-container')
    if start < 0:
        return None
    card = page[start:]
    name = re.search(r'class="wprm-recipe-name[^"]*"[^>]*>(.*?)</', card, re.DOTALL)
    name = clean(name.group(1)) if name else ""
    if name.isupper():
        name = string.capwords(name.lower())
    img = re.search(r'class="wprm-recipe-image[^"]*">\s*<img[^>]*>', card)
    image = None
    if img:
        srcset = re.search(r'srcset="([^"]+)"', img.group(0))
        if srcset:
            sizes = [c.strip().rsplit(" ", 1) for c in srcset.group(1).split(",")]
            image = max(sizes, key=lambda c: int(c[1].rstrip("w")) if len(c) > 1 else 0)[0]
        else:
            image = re.search(r'src="([^"]+)"', img.group(0)).group(1)
    ingredients = [
        re.sub(r"<[^>]+>", " ", li)
        for li in re.findall(r'<li[^>]*class="wprm-recipe-ingredient"[^>]*>(.*?)</li>', card, re.DOTALL)
    ]
    sections = []
    for group in card.split('<div class="wprm-recipe-instruction-group')[1:]:
        head = re.search(r'wprm-recipe-group-name[^>]*>(.*?)</h\d>', group.split("<li", 1)[0], re.DOTALL)
        texts = re.findall(r'class="wprm-recipe-instruction-text"[^>]*>(.*?)</div>', group, re.DOTALL)
        sections.append({
            "@type": "HowToSection",
            "name": clean(head.group(1)) if head else "",
            "itemListElement": [{"@type": "HowToStep", "text": t} for t in texts],
        })
    return {"name": name, "image": image, "recipeIngredient": ingredients, "recipeInstructions": sections}


def image_url(image):
    if isinstance(image, str):
        return image
    if isinstance(image, dict):
        return image.get("url") or image.get("contentUrl")
    if isinstance(image, list) and image:
        # Sites often list several crops; the first is usually the largest.
        return image_url(image[0])
    return None


def parse_steps(node):
    """Flatten recipeInstructions into [{"name": section, "steps": [...]}]."""
    sections = [{"name": "", "steps": []}]

    def walk(item):
        if isinstance(item, str):
            text = html.unescape(item)
            if len(NUMBERED.findall(text)) >= 2:
                text = NUMBERED.sub("\n", text)
            for line in re.split(r"\n+", text):
                if clean(line):
                    sections[-1]["steps"].append(clean(line))
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, dict):
            kind = item.get("@type")
            if kind == "HowToSection":
                sections.append({"name": clean(item.get("name", "")), "steps": []})
                walk(item.get("itemListElement", []))
            else:
                walk(item.get("text") or item.get("name") or "")

    walk(node)
    return [s for s in sections if s["steps"]]


def instagram_recipe(url):
    """Instagram posts have no recipe data; read the caption and cover photo instead."""
    code = INSTAGRAM.search(url).group(1)
    post = in_chrome(
        f"https://www.instagram.com/p/{code}/embed/captioned/",
        script="""() => ({
            caption: document.querySelector('.Caption')?.innerText || '',
            image: document.querySelector('.EmbeddedMediaImage')?.src || null,
        })""",
        wait_for=".Caption",
    )
    return recipe_from_caption(url, post["caption"], post["image"])


def recipe_from_caption(url, caption, image):
    lines = [l.strip() for l in caption.splitlines()][1:]  # first line is the account name
    lines = [l for l in lines if l]
    name, groups, steps = None, [{"name": "", "items": []}], []
    for line in lines:
        if line.startswith("View all"):
            break
        name = name or re.sub(r"[^\w)!?'’]+$", "", line)
        if m := re.match(r"[-*•]\s*(.+)", line):
            groups[-1]["items"].append(clean(m.group(1)))
        elif m := re.match(r"\d{1,2}[.)]\s+(.+)", line):
            steps.append(clean(m.group(1)))
        elif (m := re.fullmatch(r"(.{2,40}):", line)) and not steps and not re.fullmatch(
            r"ingredients|instructions|directions|method", m.group(1), re.IGNORECASE
        ):
            groups.append({"name": clean(m.group(1)), "items": []})
    groups = [g for g in groups if g["items"]]
    if not groups or not steps:
        raise ValueError("couldn't find ingredients and numbered steps in the caption")
    return {
        "id": slugify(name),
        "name": name,
        "source": url,
        "image": image,
        "ingredients": groups,
        "instructions": [{"name": "", "steps": steps}],
    }


CATEGORIES = ["Chicken", "Seafood", "Beef", "Vegetarian", "Dessert", "Breakfast"]
_WORDS = {
    "Breakfast": r"pancake|crepe|waffle|french toast|oatmeal|granola|omelet|frittata|muffin|scone",
    "Dessert": r"cookie|cake|brownie|blondie|tart|pudding|ice cream|fudge|dessert",
    "Seafood": r"salmon|shrimp|scampi|fish|cod|tuna|prawn|crab|lobster|scallop|halibut|tilapia",
    "Chicken": r"chicken|turkey",
    "Beef": r"beef|steak|birria|bolognese|burger|meatball|keftedes|pork|lamb|sirloin|brisket|chuck",
}
# Ingredients that name a meat without being one.
_NOT_MEAT = re.compile(r"broth|stock|bouillon|fish sauce|oyster sauce|anchov", re.IGNORECASE)


def guess_category(name, ingredients):
    """Best guess at the site section: dish name first, then the ingredient list."""
    for cat in ("Breakfast", "Dessert", "Seafood", "Chicken", "Beef"):
        if re.search(rf"\b(?:{_WORDS[cat]})", name, re.IGNORECASE):
            return cat
    text = " ".join(i for i in ingredients if not _NOT_MEAT.search(i))
    for cat in ("Seafood", "Chicken", "Beef"):
        if re.search(rf"\b(?:{_WORDS[cat]})", text, re.IGNORECASE):
            return cat
    return "Vegetarian"


def ingredient_groups(page, ingredients):
    """Split the flat JSON-LD list using the page's WP Recipe Maker groups (e.g. Salad / Dressing)."""
    start = page.find('<div class="wprm-recipe-ingredient-group')
    end = page.find("wprm-recipe-instructions-container", start)
    parts = page[start:end].split('<div class="wprm-recipe-ingredient-group')[1:] if start >= 0 else []
    groups = []
    for part in parts:
        head = part.split("<li", 1)[0]
        m = re.search(r'wprm-recipe-group-name[^>]*>(.*?)</h\d>', head, re.DOTALL)
        name = clean(m.group(1)).rstrip(":").strip() if m else ""
        groups.append((name, len(re.findall(r'<li[^>]*class="wprm-recipe-ingredient"', part))))
    if len(groups) < 2 or sum(n for _, n in groups) != len(ingredients):
        return [{"name": "", "items": ingredients}]
    out, i = [], 0
    for name, n in groups:
        out.append({"name": name, "items": ingredients[i:i + n]})
        i += n
    return [g for g in out if g["items"]]


def flat(groups):
    return [i for g in groups for i in g["items"]]


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "recipe"


def extract(url, page):
    recipe = recipe_from_html(page) or recipe_from_wprm(page)
    if not recipe:
        raise ValueError("no schema.org Recipe found on the page")
    name = clean(recipe.get("name", "")) or "Untitled recipe"
    ingredients = [clean(i) for i in recipe.get("recipeIngredient", []) if clean(i)]
    steps = parse_steps(recipe.get("recipeInstructions", []))
    if not ingredients or not steps:
        raise ValueError("recipe is missing ingredients or steps")
    img = image_url(recipe.get("image"))
    return {
        "id": slugify(name),
        "name": name,
        "source": url,
        "image": urllib.parse.urljoin(url, img) if img else None,
        "ingredients": ingredient_groups(page, ingredients),
        "instructions": steps,
    }


def save_image(recipe):
    """Download the dish photo so the site doesn't hotlink other websites."""
    if not recipe["image"]:
        return None
    try:
        body, content_type = fetch(recipe["image"])
    except Exception as exc:
        print(f"warn  couldn't download photo ({exc}); linking to it instead", file=sys.stderr)
        return recipe["image"]
    if not content_type.startswith("image/"):
        print(f"warn  photo URL returned {content_type}, not an image; linking to it instead", file=sys.stderr)
        return recipe["image"]
    ext = {"image/png": ".png", "image/webp": ".webp", "image/avif": ".avif"}.get(
        content_type, ".jpg"
    )
    IMAGE_DIR.mkdir(exist_ok=True)
    for old in IMAGE_DIR.glob(recipe["id"] + ".*"):
        old.unlink()
    path = IMAGE_DIR / (recipe["id"] + ext)
    path.write_bytes(body)
    return path.relative_to(ROOT).as_posix()


def read_url_list():
    lines = URL_LIST.read_text().splitlines() if URL_LIST.exists() else []
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("urls", nargs="*", help="recipe URLs (default: recipes.txt)")
    parser.add_argument("--html", help="use this saved HTML file instead of downloading")
    args = parser.parse_args(argv)

    urls = args.urls or read_url_list()
    if args.html and len(urls) != 1:
        parser.error("--html needs exactly one URL")

    existing = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else []
    by_source = {r["source"]: r for r in existing}
    failures = 0

    for url in urls:
        try:
            if INSTAGRAM.search(url) and not args.html:
                recipe = instagram_recipe(url)
            else:
                if args.html:
                    page = Path(args.html).read_text(errors="replace")
                else:
                    page = fetch_page(url)
                recipe = extract(url, page)
            taken = {r["id"] for s, r in by_source.items() if s != url}
            base, n = recipe["id"], 2
            while recipe["id"] in taken:
                recipe["id"], n = f"{base}-{n}", n + 1
            recipe["image"] = save_image(recipe)
            old = by_source.get(url, {})
            recipe["category"] = old.get("category") or guess_category(
                recipe["name"], flat(recipe["ingredients"])
            )
            by_source[url] = recipe
            print(f"ok    {recipe['name']}  [{recipe['category']}]  "
                  f"({len(flat(recipe['ingredients']))} ingredients)")
        except Exception as exc:  # keep going so one bad site doesn't stop the rest
            failures += 1
            print(f"FAIL  {url}: {exc}", file=sys.stderr)

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(list(by_source.values()), indent=2, ensure_ascii=False) + "\n")
    print(f"{len(by_source)} recipes in {DATA_FILE.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
