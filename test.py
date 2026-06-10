import psycopg2
import pymysql

print("PostgreSQL tables:")
try:
    pg_conn = psycopg2.connect(
        host="localhost", port="5432",
        database="excel_data_db", user="postgres", password=PG_PASSWORD
    )
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    for table in pg_cursor.fetchall():
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = pg_cursor.fetchone()[0]
        print(f"  {table[0]}: {count} rows")
    pg_cursor.close()
    pg_conn.close()
except Exception as e:
    print(f"  Error: {e}")

print("\nMySQL tables:")
try:
    mysql_conn = pymysql.connect(
        host="localhost", port=3306,
        database="excel_data_db", user="root", password=MYSQL_PASSWORD
    )
    mysql_cursor = mysql_conn.cursor()
    mysql_cursor.execute("SHOW TABLES")
    for table in mysql_cursor.fetchall():
        mysql_cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = mysql_cursor.fetchone()[0]
        print(f"  {table[0]}: {count} rows")
    mysql_cursor.close()
    mysql_conn.close()
except Exception as e:
    print(f"  Error: {e}")