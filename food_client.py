import requests

OFF_BASE = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "food-mcp/0.1 (contact@example.com)"}


def search_products(query: str, page: int = 1, page_size: int = 10) -> dict:
    params = {
        "action": "process",
        "json": 1,
        "search_terms": query,
        "page": page,
        "page_size": page_size,
    }

    url = f"{OFF_BASE}/cgi/search.pl"
    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()
