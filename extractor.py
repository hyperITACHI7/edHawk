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


# -----------------------------
# PURE extractors (NO logic)
# -----------------------------

def extract_single(soup, selector):
    el = soup.select_one(selector)
    return el.get_text(" ", strip=True) if el else None


def extract_by_label(soup, container_selector, label):
    for block in soup.select(container_selector):
        h = block.find("h4")
        if h and h.get_text(strip=True) == label:
            return block.get_text(" ", strip=True)
    return None


def extract_table(soup, selector):
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


def extract_blocks(soup, selector):
    return [
        el.get_text(" ", strip=True)
        for el in soup.select(selector)
        if el.get_text(strip=True)
    ]


# -----------------------------
# Orchestrator
# -----------------------------

def extract_course_data(course_url: str) -> dict:
    domain = get_domain(course_url)

    if domain not in SELECTOR_DB:
        raise ValueError(f"No selector config for {domain}")

    soup = fetch_soup(course_url)
    config = SELECTOR_DB[domain]

    data = {
        "course_url": course_url
    }

    for field, rules in config.items():

        if rules["type"] == "single":
            data[field] = extract_single(soup, rules["selector"])

        elif rules["type"] == "by_label":
            data[field] = extract_by_label(
                soup,
                rules["container_selector"],
                rules["label"]
            )

        elif rules["type"] == "table":
            data[field] = extract_table(soup, rules["selector"])

        elif rules["type"] == "blocks":
            data[field] = extract_blocks(soup, rules["selector"])

    return data

