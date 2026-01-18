import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 20


# -----------------------------
# Fetch
# -----------------------------

def fetch_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


# -----------------------------
# Your existing helper functions
# -----------------------------

def extract_by_label(soup, container_selector, label, value_selector):
    for block in soup.select(container_selector):
        h = block.find("h4")
        if h and h.get_text(strip=True) == label:
            v = block.select_one(value_selector)
            return v.get_text(" ", strip=True) if v else None
    return None


def extract_table(soup, table_selector):
    table = soup.select_one(table_selector)
    if not table:
        return None
    rows = []
    for tr in table.select("tr"):
        rows.append([td.get_text(" ", strip=True) for td in tr.select("td")])
    return rows


def extract_blocks(soup, block_configs):
    results = []
    for block in block_configs:
        for el in soup.select(block["selector"]):
            text = el.get_text(" ", strip=True)
            if all(k.lower() in text.lower() for k in block["must_contain"]):
                results.append({
                    "level": block["level"],
                    "text": text
                })
    return results


# -----------------------------
# REQUIRED orchestration function
# -----------------------------

def extract_course_data(course_url: str) -> dict:
    soup = fetch_soup(course_url)

    data = {
        "course_url": course_url,

        # Deterministic fields
        "course_name": None,
        "duration_raw": None,
        "available_intakes_raw": None,

        # Semi-structured
        "international_tuition_fee_raw": None,

        # Raw blocks (for later GPT / rules)
        "english_test_requirement_raw": None,
        "indian_entry_requirement_raw": None
    }

    # Course name
    h1 = soup.find("h1", id="headerBannerTitle")
    if h1:
        data["course_name"] = h1.get_text(strip=True)

    # Duration
    data["duration_raw"] = extract_by_label(
        soup,
        container_selector="div.e-item",
        label="Duration",
        value_selector="span"
    )

    # Intakes
    data["available_intakes_raw"] = extract_by_label(
        soup,
        container_selector="div.e-item",
        label="Start Date",
        value_selector="span"
    )

    # Tuition fee table (raw)
    data["international_tuition_fee_raw"] = extract_table(
        soup,
        table_selector="table"
    )

    # English requirement blocks
    data["english_test_requirement_raw"] = extract_blocks(
        soup,
        block_configs=[
            {
                "selector": "div#020 p.preamble",
                "must_contain": ["minimum"],
                "level": "general"
            }
        ]
    )

    # Indian entry requirement blocks
    data["indian_entry_requirement_raw"] = extract_blocks(
        soup,
        block_configs=[
            {
                "selector": "div.more",
                "must_contain": ["postgraduate"],
                "level": "postgraduate"
            }
        ]
    )

    return data
