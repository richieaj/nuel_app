import sqlite3
import os
DB_FILE = "mini.db" 
def get_db_connection():
    return sqlite3.connect(DB_FILE)
