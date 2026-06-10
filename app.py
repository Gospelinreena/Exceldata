from flask import Flask, request, jsonify
import pandas as pd
import os
import psycopg2
import pymysql
import numpy as np
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


PG_CONFIG = {
    'host': os.getenv('PG_HOST', 'localhost'),
    'port': os.getenv('PG_PORT', '5432'),
    'database': os.getenv('PG_DATABASE', 'excel_data_db'),
    'user': os.getenv('PG_USER', 'postgres'),
    'password': os.getenv('PG_PASSWORD', '')
}

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'database': os.getenv('MYSQL_DATABASE', 'excel_data_db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '')
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_and_clean_file(file_path):
    if file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='latin-1')
            except:
                df = pd.read_csv(file_path, encoding='ISO-8859-1')
    else:
        df = pd.read_excel(file_path)
    
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    df = df.replace({np.nan: None})
    df = df.where(pd.notnull(df), None)
    return df

def insert_to_postgres(df, table_name):
    conn = psycopg2.connect(**PG_CONFIG)
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
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, {columns_sql})"
    cursor.execute(create_sql)
    
    data = [tuple(row) for row in df.to_numpy()]
    placeholders = ', '.join(['%s'] * len(df.columns))
    columns_names = ', '.join([f'"{col}"' for col in df.columns])
    insert_sql = f"INSERT INTO {table_name} ({columns_names}) VALUES ({placeholders})"
    cursor.executemany(insert_sql, data)
    
    conn.commit()
    cursor.close()
    conn.close()
    return len(df)

def insert_to_mysql(df, table_name):
    conn = pymysql.connect(**MYSQL_CONFIG)
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
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, {columns_sql})"
    cursor.execute(create_sql)
    
    data = [tuple(row) for row in df.to_numpy()]
    placeholders = ', '.join(['%s'] * len(df.columns))
    columns_names = ', '.join([f'`{col}`' for col in df.columns])
    insert_sql = f"INSERT INTO {table_name} ({columns_names}) VALUES ({placeholders})"
    cursor.executemany(insert_sql, data)
    
    conn.commit()
    cursor.close()
    conn.close()
    return len(df)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'API is running'})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {ALLOWED_EXTENSIONS}'}), 400
    
    table_name = request.form.get('table_name', None)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        df = load_and_clean_file(file_path)
        
        if not table_name:
            table_name = filename.rsplit('.', 1)[0].lower()
        
        pg_rows = insert_to_postgres(df, table_name)
        mysql_rows = insert_to_mysql(df, table_name)
        
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'table_name': table_name,
            'rows': len(df),
            'columns': len(df.columns),
            'postgresql': f'{pg_rows} rows inserted',
            'mysql': f'{mysql_rows} rows inserted'
        }), 200
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

@app.route('/tables', methods=['GET'])
def list_tables():
    database = request.args.get('database', 'postgresql')
    
    try:
        if database == 'postgresql':
            conn = psycopg2.connect(**PG_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = [t[0] for t in cursor.fetchall()]
            cursor.close()
            conn.close()
            return jsonify({'database': 'postgresql', 'tables': tables})
        
        elif database == 'mysql':
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            cursor.close()
            conn.close()
            return jsonify({'database': 'mysql', 'tables': tables})
        
        else:
            return jsonify({'error': 'Invalid database. Use postgresql or mysql'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tables/<table_name>/count', methods=['GET'])
def get_row_count(table_name):
    database = request.args.get('database', 'postgresql')
    
    try:
        if database == 'postgresql':
            conn = psycopg2.connect(**PG_CONFIG)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return jsonify({'table': table_name, 'database': 'postgresql', 'rows': count})
        
        elif database == 'mysql':
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return jsonify({'table': table_name, 'database': 'mysql', 'rows': count})
        
        else:
            return jsonify({'error': 'Invalid database'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tables/<table_name>/data', methods=['GET'])
def get_table_data(table_name):
    database = request.args.get('database', 'postgresql')
    limit = request.args.get('limit', 100, type=int)
    
    try:
        if database == 'postgresql':
            conn = psycopg2.connect(**PG_CONFIG)
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return jsonify({
                'table': table_name,
                'database': 'postgresql',
                'rows_returned': len(df),
                'data': df.to_dict(orient='records')
            })
        
        elif database == 'mysql':
            conn = pymysql.connect(**MYSQL_CONFIG)
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return jsonify({
                'table': table_name,
                'database': 'mysql',
                'rows_returned': len(df),
                'data': df.to_dict(orient='records')
            })
        
        else:
            return jsonify({'error': 'Invalid database'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tables/<table_name>', methods=['DELETE'])
def delete_table(table_name):
    database = request.args.get('database', 'postgresql')
    
    try:
        if database == 'postgresql':
            conn = psycopg2.connect(**PG_CONFIG)
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': f'Table {table_name} deleted from PostgreSQL'})
        
        elif database == 'mysql':
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': f'Table {table_name} deleted from MySQL'})
        
        else:
            return jsonify({'error': 'Invalid database'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/tables/<table_name>/search', methods=['GET'])
def search_table(table_name):
    database = request.args.get('database', 'postgresql')
    column = request.args.get('column')
    value = request.args.get('value')
    
    if not column or not value:
        return jsonify({'error': 'Provide column and value parameters'}), 400
    
    try:
        if database == 'postgresql':
            conn = psycopg2.connect(**PG_CONFIG)
            query = f"SELECT * FROM {table_name} WHERE {column}::text LIKE '%{value}%' LIMIT 50"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return jsonify({
                'table': table_name,
                'database': 'postgresql',
                'search_column': column,
                'search_value': value,
                'results': len(df),
                'data': df.to_dict(orient='records')
            })
        
        elif database == 'mysql':
            conn = pymysql.connect(**MYSQL_CONFIG)
            query = f"SELECT * FROM {table_name} WHERE {column} LIKE '%{value}%' LIMIT 50"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return jsonify({
                'table': table_name,
                'database': 'mysql',
                'search_column': column,
                'search_value': value,
                'results': len(df),
                'data': df.to_dict(orient='records')
            })
        
        else:
            return jsonify({'error': 'Invalid database'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)