import snowflake.connector
from .query_loader import load_query_template
from .snowflake_client import connect_to_snowflake
import logging

def fetch_reviews(sku: str, batch_size: int = 15000):
    print(f"fetch_reviews called for SKU: {sku}")
    logging.info(f"fetch_reviews called for SKU: {sku}")
    query_template = load_query_template("fetch_reviews")
    query = query_template.format(sku=sku)
    logging.info(f"Executing Snowflake query: {query}")
    conn = connect_to_snowflake()
    cursor = conn.cursor()
    cursor.execute(query)
    review_count = 0
    first_reviews = []
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        for row in rows:
            # row: (sku, customer_review, product_rating, created_date, mc1, mc2, mc3, product_description_short, product_name, product_id, product_link)
            review = {
                "sku": row[0],
                "customer_review": row[1],
                "product_rating": row[2],
                "created_date": row[3],
                "mc1": row[4],
                "mc2": row[5],
                "mc3": row[6],
                "product_description_short": row[7],
                "product_name": row[8],
                "product_id": row[9],
                "product_link": row[10]
            }
            if review_count < 3:
                first_reviews.append(review)
            review_count += 1
            yield review
    if first_reviews:
        logging.info(f"First 3 reviews fetched: {first_reviews}")
    logging.info(f"Total reviews fetched: {review_count}")
    cursor.close()
    conn.close() 