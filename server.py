from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("food-mcp")

OFF_BASE = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "food-mcp/0.1 (contact@example.com)"}


async def search_products(query: str, page: int = 1, page_size: int = 10) -> dict:
    params = {
        "action": "process",
        "json": 1,
        "search_terms": query,
        "page": page,
        "page_size": page_size,
    }

    url = f"{OFF_BASE}/cgi/search.pl"

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params, headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def food_search(
    query: str,
    page: int = 1,
    page_size: int = 10,
) -> list[dict]:
    """
    Search food products using Open Food Facts.
    """
    data = await search_products(query, page, page_size)

    results = []
    for p in data.get("products", [])[:page_size]:
        nutriments = p.get("nutriments", {})
        results.append(
            {
                "name": p.get("product_name"),
                "brand": p.get("brands"),
                "nutriscore": p.get("nutriscore_grade"),
                "nova_group": p.get("nova_group"),
                "sugars_100g": nutriments.get("sugars_100g"),
            }
        )

    return results


def pick_products(products: list[dict]) -> dict | None:

    for p in products:
        if p.get("product_name"):
            return p
    return None


@mcp.tool()
async def food_label_explainer(
    query: str,
    page_size: int = 10,
) -> dict | None:

    data = await search_products(query=query, page_size=page_size)
    products = data.get("products", [])

    product = pick_products(products)

    if not product:
        return None

    product_name = product.get("product_name")
    brand = product.get("brands")

    nutriscore = product.get("nutriscore_grade")
    if nutriscore:
        nutriscore = nutriscore.lower()

    nutriments = product.get("nutriments", {})
    nova_group = product.get("nova_group")
    nova_explanation = None

    sugar_100g = nutriments.get("sugars_100g")
    # 6. Classify sugar level
    sugar_level = None

    try:
        sugar_value = float(sugar_100g)
        if sugar_value < 5:
            sugar_level = "low"
        elif sugar_value <= 12.5:
            sugar_level = "moderate"
        else:
            sugar_level = "high"
    except (TypeError, ValueError):
        sugar_value = None

    summary_parts = []

    if sugar_value is not None and sugar_level:
        summary_parts.append(
            f"It contains about {sugar_value}g of sugar per 100g, which is considered {sugar_level}."
        )

    summary = (
        " ".join(summary_parts)
        if summary_parts
        else "No detailed label information is available."
    )

    return {
        "product_name": product_name,
        "brand": brand,
        "nutriscore": nutriscore.upper() if nutriscore else None,
        "nova_group": nova_group,
        "nova_explanation": nova_explanation,
        "sugar_100g": sugar_value,
        "sugar_level": sugar_level,
        "summary": summary,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
