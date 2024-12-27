from flask import Flask
import mysql.connector

app = Flask(__name__)

# Database Configuration
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Krishna1919@"
DB_NAME = "db1"

app.secret_key = "your_secret_key"

def get_db_connection():
    """Establish and return a database connection."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )