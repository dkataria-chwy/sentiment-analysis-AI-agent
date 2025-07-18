import pytest
from core.snowflake_client import connect_to_snowflake, execute_query

def test_snowflake_connection_and_query():
    conn = connect_to_snowflake()
    try:
        results = execute_query(conn, "SELECT 1 AS test_col")
        assert isinstance(results, list)
        assert len(results) == 1
        assert 'TEST_COL' in results[0] or 'test_col' in results[0]
        assert results[0].get('TEST_COL', results[0].get('test_col')) == 1
    finally:
        conn.close()
