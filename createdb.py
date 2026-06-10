import psycopg2
import pymysql

try:
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="postgres",
        user="postgres",
        password=PG_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE excel_data_db")
    print("PostgreSQL database created")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"PostgreSQL error: {e}")

try:
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password=MYSQL_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS excel_data_db")
    print("MySQL database created")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"MySQL error: {e}")