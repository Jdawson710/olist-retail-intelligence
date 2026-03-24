import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
VISUALS_DIR = BASE_DIR / "visuals"

# Load datasets
customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
geolocation = pd.read_csv(DATA_DIR / "olist_geolocation_dataset.csv")
order_items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
reviews = pd.read_csv(DATA_DIR / "olist_order_reviews_dataset.csv")
orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
products = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
sellers = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
category_translation = pd.read_csv(DATA_DIR / "product_category_name_translation.csv")


datasets = {
    "customers": customers,
    "geolocation": geolocation,
    "order_items": order_items,
    "payments": payments,
    "reviews": reviews,
    "orders": orders,
    "products": products,
    "sellers": sellers,
    "category_translation": category_translation
}

for name, df in datasets.items():
    print(f"\n--- {name.upper()} ---")
    print("Shape:", df.shape)
    print("\nMissing values:")
    print(df.isnull().sum())
    print("\nDuplicates:", df.duplicated().sum())

    customers["customer_zip_code_prefix"] = customers["customer_zip_code_prefix"].astype(str).str.zfill(5)
customers["customer_city"] = customers["customer_city"].astype(str).str.strip().str.lower()
customers["customer_state"] = customers["customer_state"].astype(str).str.strip().str.upper()

customers_clean = customers.copy()

sellers["seller_zip_code_prefix"] = sellers["seller_zip_code_prefix"].astype(str).str.zfill(5)
sellers["seller_city"] = sellers["seller_city"].astype(str).str.strip().str.lower()
sellers["seller_state"] = sellers["seller_state"].astype(str).str.strip().str.upper()

sellers_clean = sellers.copy()

geolocation["geolocation_zip_code_prefix"] = geolocation["geolocation_zip_code_prefix"].astype(str).str.zfill(5)
geolocation["geolocation_city"] = geolocation["geolocation_city"].astype(str).str.strip().str.lower()
geolocation["geolocation_state"] = geolocation["geolocation_state"].astype(str).str.strip().str.upper()

geo_clean = geolocation.groupby("geolocation_zip_code_prefix", as_index=False).agg({
    "geolocation_lat": "mean",
    "geolocation_lng": "mean",
    "geolocation_city": "first",
    "geolocation_state": "first"
})


order_date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for col in order_date_cols:
    orders[col] = pd.to_datetime(orders[col], errors="coerce")

orders["order_month"] = orders["order_purchase_timestamp"].dt.to_period("M").astype(str)

orders_clean = orders.copy()

delivered_orders = orders_clean[
    (orders_clean["order_status"] == "delivered") &
    (orders_clean["order_delivered_customer_date"].notna()) &
    (orders_clean["order_estimated_delivery_date"].notna()) &
    (orders_clean["order_purchase_timestamp"].notna())
].copy()

delivered_orders["actual_delivery_days"] = (
    delivered_orders["order_delivered_customer_date"] -
    delivered_orders["order_purchase_timestamp"]
).dt.days

delivered_orders["estimated_delivery_days"] = (
    delivered_orders["order_estimated_delivery_date"] -
    delivered_orders["order_purchase_timestamp"]
).dt.days

delivered_orders["delivery_lag_days"] = (
    delivered_orders["actual_delivery_days"] -
    delivered_orders["estimated_delivery_days"]
)

order_items["shipping_limit_date"] = pd.to_datetime(order_items["shipping_limit_date"], errors="coerce")

order_items_clean = order_items[
    (order_items["price"] > 0) &
    (order_items["freight_value"] >= 0)
].copy()

order_items_clean = order_items_clean.drop_duplicates()

order_items_clean["total_item_value"] = (
    order_items_clean["price"] + order_items_clean["freight_value"]
)

order_items_clean["freight_ratio"] = (
    order_items_clean["freight_value"] / order_items_clean["price"]
)

payments_clean = payments[payments["payment_value"] >= 0].copy()
payments_clean["payment_type"] = payments_clean["payment_type"].astype(str).str.strip().str.lower()

review_date_cols = [
    "review_creation_date",
    "review_answer_timestamp"
]

for col in review_date_cols:
    reviews[col] = pd.to_datetime(reviews[col], errors="coerce")

reviews_clean = reviews[
    (reviews["review_score"] >= 1) &
    (reviews["review_score"] <= 5)
].copy()

reviews_clean = reviews_clean.sort_values("review_answer_timestamp").drop_duplicates("order_id", keep="last")

products["product_category_name"] = products["product_category_name"].astype(str).str.strip().str.lower()

product_num_cols = [
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
]

for col in product_num_cols:
    products[col] = products[col].fillna(products[col].median())

category_translation["product_category_name"] = category_translation["product_category_name"].astype(str).str.strip().str.lower()
category_translation["product_category_name_english"] = category_translation["product_category_name_english"].astype(str).str.strip().str.lower()

products_clean = products.merge(
    category_translation,
    on="product_category_name",
    how="left"
)

products_clean["product_category_name_english"] = products_clean["product_category_name_english"].fillna("unknown")

print("\n--- RELATIONSHIP CHECKS ---")
print("order_items -> orders:", order_items_clean["order_id"].isin(orders_clean["order_id"]).mean())
print("orders -> customers:", orders_clean["customer_id"].isin(customers_clean["customer_id"]).mean())
print("order_items -> products:", order_items_clean["product_id"].isin(products_clean["product_id"]).mean())
print("order_items -> sellers:", order_items_clean["seller_id"].isin(sellers_clean["seller_id"]).mean())
print("payments -> orders:", payments_clean["order_id"].isin(orders_clean["order_id"]).mean())
print("reviews -> orders:", reviews_clean["order_id"].isin(orders_clean["order_id"]).mean())

monthly_orders = orders_clean.groupby("order_month")["order_id"].count()

plt.figure(figsize=(12, 6))
monthly_orders.plot()
plt.title("Orders per Month")
plt.xlabel("Month")
plt.ylabel("Number of Orders")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(VISUALS_DIR / "orders_per_month.png")
plt.close()

plt.figure(figsize=(8, 6))
plt.boxplot(
    [
        delivered_orders["estimated_delivery_days"].dropna(),
        delivered_orders["actual_delivery_days"].dropna()
    ],
    labels=["Estimated", "Actual"]
)
plt.title("Estimated vs Actual Delivery Days")
plt.ylabel("Days")
plt.tight_layout()
plt.savefig(VISUALS_DIR / "delivery_performance_boxplot.png")
plt.close()

review_counts = reviews_clean["review_score"].value_counts().sort_index()

plt.figure(figsize=(8, 5))
review_counts.plot(kind="bar")
plt.title("Review Score Distribution")
plt.xlabel("Review Score")
plt.ylabel("Count")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(VISUALS_DIR / "review_score_distribution.png")
plt.close()