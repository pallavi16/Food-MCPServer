from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from food_client import search_products
from models import SearchInput

app = FastAPI(title="Food MCP")

# ---- TOOL IMPLEMENTATIONS ----


def tool_food_search(params: dict):
    input = SearchInput(**params)

    data = search_products(
        query=input.query,
        page=input.page,
        page_size=input.page_size,
    )

    results = []
    for p in data.get("products", [])[: input.page_size]:
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


# ---- TOOL REGISTRY ----

TOOLS = {"food.search": tool_food_search}

# ---- MCP ENDPOINT ----


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    body = await request.json()

    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    if method not in TOOLS:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"},
            }
        )

    try:
        result = TOOLS[method](params)
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
        )
    except Exception as e:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": str(e),
                },
            }
        )


# ---- DISCOVERY ----


@app.get("/.well-known/mcp.json")
def discovery():
    return {
        "name": "food-mcp",
        "version": "0.1.0",
        "tools": [
            {
                "name": "food.search",
                "description": "Search food products using Open Food Facts",
                "input_schema": {
                    "query": "string",
                    "page": "integer",
                    "page_size": "integer",
                },
            }
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
