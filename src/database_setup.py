# src/database_setup.py
from cryptography.fernet import Fernet
import sqlite3
import os

def setup_database():
    # Crear o conectar a una base de datos
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()

    # Crear una tabla si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords
                      (id INTEGER PRIMARY KEY, service TEXT, username TEXT, password TEXT)''')

    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()

    # Generar y guardar la clave de cifrado si no existe
    if not os.path.exists("secret.key"):
        with open("secret.key", "wb") as key_file:
            key_file.write(Fernet.generate_key())
