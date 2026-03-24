# =========================
# IMPORTS
# =========================
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.types import VARCHAR, Integer, DECIMAL, DateTime, Float

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# =========================
# LOAD DATA
# =========================
customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
geolocation = pd.read_csv(DATA_DIR / "olist_geolocation_dataset.csv")
order_items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
reviews = pd.read_csv(DATA_DIR / "olist_order_reviews_dataset.csv")
orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
products = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
sellers = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
category_translation = pd.read_csv(DATA_DIR / "product_category_name_translation.csv")

# =========================
# CLEANING
# =========================

# --- Convert datetime columns ---
date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for col in date_cols:
    orders[col] = pd.to_datetime(orders[col], errors='coerce')

# --- Price validation ---
order_items = order_items[order_items['price'] > 0]

# --- Fix zip code formatting ---
customers['customer_zip_code_prefix'] = customers['customer_zip_code_prefix'].astype(str)
sellers['seller_zip_code_prefix'] = sellers['seller_zip_code_prefix'].astype(str)

# --- Handle missing product category ---
products['product_category_name'] = products['product_category_name'].fillna("unknown")

# =========================
# MYSQL CONNECTION
# =========================

# ⚠️ REPLACE WITH YOUR PASSWORD
engine = create_engine("mysql+pymysql://root:root@localhost/olist_intelligence")

# =========================
# LOAD TO MYSQL
# =========================

customers.to_sql("customers", engine, if_exists="replace", index=False,
                 dtype={"customer_id": VARCHAR(50)})

orders.to_sql("orders", engine, if_exists="replace", index=False)

order_items.to_sql("order_items", engine, if_exists="replace", index=False,
                   dtype={"price": DECIMAL(10,2), "freight_value": DECIMAL(10,2)})

payments.to_sql("payments", engine, if_exists="replace", index=False)

reviews.to_sql("reviews", engine, if_exists="replace", index=False)

products.to_sql("products", engine, if_exists="replace", index=False)

sellers.to_sql("sellers", engine, if_exists="replace", index=False)

category_translation.to_sql("category_translation", engine, if_exists="replace", index=False)

print("\n✅ ETL PIPELINE COMPLETED SUCCESSFULLY!")