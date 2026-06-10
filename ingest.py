import pandas as pd
import os
import psycopg2
import pymysql
import numpy as np

DATA_FOLDER = "test_data"

PG_HOST = "localhost"
PG_PORT = "5432"
PG_DATABASE = "excel_data_db"
PG_USER = "postgres"

MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DATABASE = "excel_data_db"
MYSQL_USER = "root"

def get_csv_files(folder):
    files = []
    for file in os.listdir(folder):
        if file.endswith('.csv'):
            files.append(os.path.join(folder, file))
    return files

def get_table_name(file_path):
    name = os.path.basename(file_path)
    name = name.replace('.csv', '').lower()
    name = name.replace(' ', '_').replace('-', '_')
    return name

def load_and_clean_csv(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='latin-1')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='ISO-8859-1')
    
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    df = df.replace({np.nan: None})
    df = df.where(pd.notnull(df), None)
    return df

def create_postgres_table(conn, df, table_name):
    cursor = conn.cursor()
    
    columns = []
    for col, dtype in df.dtypes.items():
        if dtype == 'int64':
            sql_type = 'INTEGER'
        elif dtype == 'float64':
            sql_type = 'FLOAT'
        else:
            sql_type = 'TEXT'
        columns.append(f'"{col}" {sql_type}')
    
    columns_sql = ', '.join(columns)
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, {columns_sql})"
    
    cursor.execute(sql)
    conn.commit()
    cursor.close()

def insert_postgres(conn, df, table_name):
    cursor = conn.cursor()
    
    data = [tuple(row) for row in df.to_numpy()]
    columns = ', '.join([f'"{col}"' for col in df.columns])
    placeholders = ', '.join(['%s'] * len(df.columns))
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    cursor.executemany(sql, data)
    conn.commit()
    cursor.close()

def create_mysql_table(conn, df, table_name):
    cursor = conn.cursor()
    
    columns = []
    for col, dtype in df.dtypes.items():
        if dtype == 'int64':
            sql_type = 'INT'
        elif dtype == 'float64':
            sql_type = 'FLOAT'
        else:
            sql_type = 'TEXT'
        columns.append(f'`{col}` {sql_type}')
    
    columns_sql = ', '.join(columns)
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, {columns_sql})"
    
    cursor.execute(sql)
    conn.commit()
    cursor.close()

def insert_mysql(conn, df, table_name):
    cursor = conn.cursor()
    
    data = [tuple(row) for row in df.to_numpy()]
    columns = ', '.join([f'`{col}`' for col in df.columns])
    placeholders = ', '.join(['%s'] * len(df.columns))
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    cursor.executemany(sql, data)
    conn.commit()
    cursor.close()

def main():
    files = get_csv_files(DATA_FOLDER)
    print(f"Found {len(files)} files")
    
    try:
        pg_conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT,
            database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD
        )
        print("PostgreSQL connected")
    except Exception as e:
        print(f"PostgreSQL error: {e}")
        pg_conn = None
    
    try:
        mysql_conn = pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            database=MYSQL_DATABASE, user=MYSQL_USER, password=MYSQL_PASSWORD
        )
        print("MySQL connected")
    except Exception as e:
        print(f"MySQL error: {e}")
        mysql_conn = None
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        table_name = get_table_name(file_path)
        
        print(f"\nProcessing: {file_name}")
        
        df = load_and_clean_csv(file_path)
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        
        if pg_conn:
            create_postgres_table(pg_conn, df, table_name)
            insert_postgres(pg_conn, df, table_name)
            print(f"  PostgreSQL: {len(df)} rows inserted")
        
        if mysql_conn:
            create_mysql_table(mysql_conn, df, table_name)
            insert_mysql(mysql_conn, df, table_name)
            print(f"  MySQL: {len(df)} rows inserted")
    
    if pg_conn:
        pg_conn.close()
    if mysql_conn:
        mysql_conn.close()
    
    print("\nDone")

if __name__ == "__main__":
    main()