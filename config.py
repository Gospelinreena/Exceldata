# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    PG_HOST = os.getenv('PG_HOST', 'localhost')
    PG_PORT = os.getenv('PG_PORT', '5432')
    PG_DATABASE = os.getenv('PG_DATABASE', 'excel_data_db')
    PG_USER = os.getenv('PG_USER', 'postgres')
    PG_PASSWORD = os.getenv('PG_PASSWORD', '')
    
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'excel_data_db')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    
    @property
    def PG_CONFIG(self):
        return {
            'host': self.PG_HOST,
            'port': self.PG_PORT,
            'database': self.PG_DATABASE,
            'user': self.PG_USER,
            'password': self.PG_PASSWORD
        }
    
    @property
    def MYSQL_CONFIG(self):
        return {
            'host': self.MYSQL_HOST,
            'port': self.MYSQL_PORT,
            'database': self.MYSQL_DATABASE,
            'user': self.MYSQL_USER,
            'password': self.MYSQL_PASSWORD
        }