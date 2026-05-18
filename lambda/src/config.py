import os

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

# --------------------------------------------------
# AUTH
# --------------------------------------------------
TOKEN_BOTAFOGO = os.getenv("TOKEN_BOTAFOGO")
TOKEN_BARRA = os.getenv("TOKEN_BARRA")
TOKEN_TIJUCA = os.getenv("TOKEN_TIJUCA")
TOKEN_LEBLON = os.getenv("TOKEN_LEBLON")

# --------------------------------------------------
# API URLS
# --------------------------------------------------
API_SALES = "https://data.saipos.io/v1/search_sales"
API_SALES_ITEMS = "https://data.saipos.io/v1/sales_items"
API_INVENTORY_MOVEMENTS = "https://data.saipos.io/v1/search_ingredient_movement"

# --------------------------------------------------
# PAGINATION DEFAULTS
# --------------------------------------------------
DEFAULT_LIMIT = 500
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 5

# --------------------------------------------------
# LANDING BUCKET
# --------------------------------------------------
LANDING_BUCKET = "ducadu-landing"

LANDING_SALES = "sales"
LANDING_SALES_ITEMS = "sales_items"
LANDING_INVENTORY = "inventory"

def build_headers(token: str) -> dict:

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

STORE_TOKENS = {
    "botafogo": TOKEN_BOTAFOGO,
    "barra": TOKEN_BARRA,
    "tijuca": TOKEN_TIJUCA,
    "leblon": TOKEN_LEBLON,
}
