from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("shopify")

# Shopify API configuration
SHOPIFY_STORE = "datapal-shop"  # e.g. mystore
SHOPIFY_ACCESS_TOKEN = "5663ee1b98dcc59c7655a40697e40c68"
SHOPIFY_API_BASE = f"https://ottomate.shop/"

# Shopify request helper
async def make_shopify_request(endpoint: str) -> dict[str, Any] | None:
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SHOPIFY_API_BASE}/{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
        
async def storefront_query(query: str, variables: dict = {}) -> dict:
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SHOPIFY_API_BASE}/{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
        
async def storefront_query(query: str, variables: dict = {}) -> dict:
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SHOPIFY_API_BASE}/api/2025-04/graphql.json",
                headers=headers,
                json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            data = response.json()
            print(data) 
            return data
        except Exception as e:
            print(f"GraphQL request error: {e}")
            return {"error": str(e)}

        
@mcp.tool()
async def list_products(limit: int = 5) -> str:
    """List the first few products from the store."""
    data = await make_shopify_request(f"products.json?limit={limit}")
    if not data or "products" not in data:
        return "No products found or failed to fetch."

    products = data["products"]
    return "\n---\n".join([f"{p['title']}: {p.get('body_html', '')[:100]}" for p in products])

@mcp.tool()
async def price_list(limit: int = 5) -> str:
    """List product titles with their prices."""
    data = await make_shopify_request(f"products.json?limit={limit}")
    if not data or "products" not in data:
        return "No products found or failed to fetch."

    result = []
    for product in data["products"]:
        title = product["title"]
        try:
            price = product["variants"][0]["price"]
        except (IndexError, KeyError):
            price = "Unknown"
        result.append(f"{title} - GBP{price}")
    return "\n".join(result)

@mcp.tool()
async def create_cart(variant_id: str, quantity: int = 1) -> str:
    """Create a new cart with a product variant"""
    query = """
    mutation createCart($lines: [CartLineInput!]!) {
      cartCreate(input: { lines: $lines }) {
        cart {
          id
          checkoutUrl
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {
        "lines": [
            {
                "merchandiseId": variant_id,
                "quantity": quantity
            }
        ]
    }

    data = await storefront_query(query, variables)

    if errors := data.get("data", {}).get("cartCreate", {}).get("userErrors"):
        return f"Cart creation failed: {errors}"

    cart = data["data"]["cartCreate"]["cart"]
    return f" Cart created!\nCart ID: {cart['id']}\nCheckout here: {cart['checkoutUrl']}"

@mcp.tool()
async def add_to_cart(cart_id: str, variant_id: str, quantity: int = 1) -> str:
    """Add item to an existing cart."""
    query = """
    mutation addCartLines($cartId: ID!, $lines: [CartLineInput!]!) {
      cartLinesAdd(cartId: $cartId, lines: $lines) {
        cart {
          id
          checkoutUrl
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {
        "cartId": cart_id,
        "lines": [
            {
                "merchandiseId": variant_id,
                "quantity": quantity
            }
        ]
    }

    data = await storefront_query(query, variables)
    errors = data.get("data", {}).get("cartLinesAdd", {}).get("userErrors")
    if errors:
        return f"Failed to add item: {errors}"

    return f"Added to cart. Checkout here: {data['data']['cartLinesAdd']['cart']['checkoutUrl']}"

@mcp.tool()
def rate_us(stars: int, comment: str = "") -> str:
    """Submit a rating (1 to 5 stars) with optional comment."""
    if not 1 <= stars <= 5:
        return "Please provide a rating between 1 and 5 stars."
    ratings.append((stars, comment))
    return f"Thanks for rating us {stars} star(s)!"


if __name__ == "__main__":
    print("Server is running...")
    mcp.run(transport='stdio')
