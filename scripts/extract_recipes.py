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
import html
import json
import os
import re
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
TAG = re.compile(r"<[^>]+>")
# "1. Preheat oven.2. Toss..." -> split before each "N." that starts a sentence.
NUMBERED = re.compile(r"(?:^|(?<=[.!?)]))\s*\d{1,2}\.\s*(?=[A-Z])")


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(), resp.headers.get_content_type()


def fetch_page(url):
    try:
        return fetch(url)[0].decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 503):
            raise
    # Bot protection (e.g. Cloudflare): load the page in a real Chrome window.
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
        page.wait_for_timeout(1500)
        content = page.content()
        browser.close()
    return content


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


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "recipe"


def extract(url, page):
    recipe = recipe_from_html(page)
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
        "ingredients": ingredients,
        "instructions": steps,
    }


def save_image(recipe):
    """Download the dish photo so the site doesn't hotlink other websites."""
    if not recipe["image"]:
        return None
    body, content_type = fetch(recipe["image"])
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
            by_source[url] = recipe
            print(f"ok    {recipe['name']}  ({len(recipe['ingredients'])} ingredients)")
        except Exception as exc:  # keep going so one bad site doesn't stop the rest
            failures += 1
            print(f"FAIL  {url}: {exc}", file=sys.stderr)

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(list(by_source.values()), indent=2, ensure_ascii=False) + "\n")
    print(f"{len(by_source)} recipes in {DATA_FILE.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
