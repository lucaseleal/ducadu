import os

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
DATABASE_URL          = os.getenv("DATABASE_URL")

# --------------------------------------------------
# GOOGLE SHEETS
# --------------------------------------------------
SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
GOOGLE_SA_JSON_B64    = os.getenv("GOOGLE_SA_JSON_B64")

# --------------------------------------------------
# IFOOD
# --------------------------------------------------
IFOOD_CLIENT_ID = os.getenv("IFOOD_CLIENT_ID")
IFOOD_CLIENT_SECRET = os.getenv("IFOOD_CLIENT_SECRET")
IFOOD_API_BASE = os.getenv("IFOOD_API_BASE", "https://merchant-api.ifood.com.br")
IFOOD_AUTH_URL = f"{IFOOD_API_BASE.rstrip('/')}/authentication/v1.0/oauth/token"
IFOOD_USE_HOMOLOGATION_HEADER = os.getenv("IFOOD_USE_HOMOLOGATION", "true").lower() in (
    "1",
    "true",
    "yes",
)

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
API_SALES_STATUS_HISTORIES = "https://data.saipos.io/v1/sales_status_histories"
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
LANDING_SALES_STATUS_HISTORIES = "sales_status_histories"
LANDING_INVENTORY = "inventory"
LANDING_IFOOD_SALES = "ifood_sales"
LANDING_IFOOD_REVIEWS = "ifood_reviews"
LANDING_IFOOD_ANALYTICS = "ifood_analytics"
LANDING_IFOOD_REVIEW_SUMMARY = "ifood_review_summary"

# Comma-separated merchant UUIDs; empty = all merchants returned by GET /merchants
IFOOD_MERCHANT_IDS = [
    m.strip()
    for m in (os.getenv("IFOOD_MERCHANT_IDS") or "").split(",")
    if m.strip()
]

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
