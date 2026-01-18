import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 20

# -----------------------------
# Load selector registry ONCE
# -----------------------------

with open("selectors.json", "r", encoding="utf-8") as f:
    SELECTOR_DB = json.load(f)

# -----------------------------
# Utilities
# -----------------------------

def get_domain(course_url: str) -> str:
    return urlparse(course_url).netloc.replace("www.", "")


def fetch_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def safe_select(soup, selector):
    try:
        return soup.select(selector)
    except Exception:
        return []


# -----------------------------
# PURE extractors (NO logic)
# -----------------------------

def extract_single(soup, selector):
    try:
        el = soup.select_one(selector)
        return el.get_text(" ", strip=True) if el else None
    except Exception:
        return None


def extract_by_label(soup, container_selector, label):
    try:
        for block in soup.select(container_selector):
            h = block.find("h4")
            if h and h.get_text(strip=True) == label:
                return block.get_text(" ", strip=True)
    except Exception:
        pass
    return None


def extract_table(soup, selector):
    try:
        table = soup.select_one(selector)
        if not table:
            return None

        rows = []
        for tr in table.select("tr"):
            rows.append([
                td.get_text(" ", strip=True)
                for td in tr.select("td")
            ])
        return rows
    except Exception:
        return None


def extract_blocks(soup, selector):
    elements = safe_select(soup, selector)
    return [
        el.get_text(" ", strip=True)
        for el in elements
        if el.get_text(strip=True)
    ]


# -----------------------------
# Generic extractor dispatcher
# -----------------------------

def apply_extractor(soup, rules):
    extractor_type = rules.get("type")

    if extractor_type == "single":
        return extract_single(soup, rules["selector"])

    if extractor_type == "by_label":
        return extract_by_label(
            soup,
            rules["container_selector"],
            rules["label"]
        )

    if extractor_type == "table":
        return extract_table(soup, rules["selector"])

    if extractor_type == "blocks":
        return extract_blocks(soup, rules["selector"])

    return None


# -----------------------------
# Orchestrator (PRIMARY → FALLBACK)
# -----------------------------

def extract_course_data(course_url: str) -> dict:
    domain = get_domain(course_url)

    if domain not in SELECTOR_DB:
        raise ValueError(f"No selector config for {domain}")

    course_soup = fetch_soup(course_url)
    config = SELECTOR_DB[domain]

    data = {
        "course_url": course_url
    }

    for field, rule_set in config.items():

        result = None

        # ---------- PRIMARY ----------
        primary = rule_set.get("primary")
        if primary:
            if primary.get("source") == "external":
                soup = fetch_soup(primary["url"])
            else:
                soup = course_soup

            result = apply_extractor(soup, primary)

        # ---------- FALLBACK ----------
        if is_empty(result):
            fallback = rule_set.get("fallback")
            if fallback:
                soup = fetch_soup(fallback["url"])
                result = apply_extractor(soup, fallback)

        data[field] = result

    return data
