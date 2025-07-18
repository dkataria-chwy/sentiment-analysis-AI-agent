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
            # row: (sku, customer_review, product_rating, created_date)
            review = {
                "sku": row[0],
                "customer_review": row[1],  # can be None
                "product_rating": row[2],
                "created_date": row[3]
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