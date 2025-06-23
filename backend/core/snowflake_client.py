import snowflake.connector
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import logging

def connect_to_snowflake() -> snowflake.connector.SnowflakeConnection:
    """
    Establishes a connection to Snowflake using SSO authentication.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials from environment variables
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    user = os.getenv('SNOWFLAKE_USER')
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
    database = os.getenv('SNOWFLAKE_DATABASE')
    schema = os.getenv('SNOWFLAKE_SCHEMA')
    role = os.getenv('SNOWFLAKE_ROLE')
    okta_url = os.getenv('SNOWFLAKE_OKTA_URL')
    logging.info('Attempting to connect to Snowflake account=%s user=%s warehouse=%s database=%s schema=%s role=%s okta_url=%s', account, user, warehouse, database, schema, role, okta_url)
    
    # Create connection using SSO
    try:
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            authenticator='externalbrowser',  # Use SSO authentication
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role,
            okta_url=okta_url
        )
        logging.info('Successfully connected to Snowflake.')
        return conn
    except Exception as e:
        logging.error('Error connecting to Snowflake: %s', str(e), exc_info=True)
        raise

def execute_query(conn: snowflake.connector.SnowflakeConnection, query: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL query and returns the results as a list of dictionaries.
    """
    logging.info('Executing query: %s', query)
    try:
        cursor = conn.cursor(snowflake.connector.DictCursor)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        logging.info('Query executed successfully, %d rows returned.', len(results))
        return results
    except Exception as e:
        logging.error('Error executing query: %s', str(e), exc_info=True)
        raise

def main():
    # Example query - replace with your actual query
    query = """
    SELECT * FROM edldb.sc_user_tools_analytics_sandbox.uta_mc1_mc2_occams_forecast_herald limit 10
    """
    
    try:
        logging.info('Starting main Snowflake test.')
        # Connect to Snowflake
        conn = connect_to_snowflake()
        results = execute_query(conn, query)
        logging.info('Query Results:')
        for row in results:
            logging.info(row)
            
    except Exception as e:
        logging.error('An error occurred: %s', str(e), exc_info=True)
    finally:
        if 'conn' in locals():
            conn.close()
            logging.info('Connection closed.')

if __name__ == "__main__":
    main() 
 