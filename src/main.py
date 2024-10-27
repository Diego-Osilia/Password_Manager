from database_setup import setup_database
import sqlite3
import tkinter as tk
from tkinter import messagebox
from cryptography.fernet import Fernet
import os

# Configuración inicial de la base de datos
setup_database()

# Cargar la clave de cifrado
def load_key():
    if not os.path.exists("secret.key"):
        generate_key()
    
    with open("secret.key", "rb") as key_file:
        return key_file.read()

# Generar una nueva clave de cifrado
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Inicializar el cifrador con la clave cargada
cipher = Fernet(load_key())

# Conexión a la base de datos
def connect_db():
    return sqlite3.connect('password_manager.db')

# Función para encriptar una contraseña
def encrypt_password(password):
    return cipher.encrypt(password.encode()).decode()

# Función para desencriptar una contraseña
def decrypt_password(encrypted_password):
    return cipher.decrypt(encrypted_password.encode()).decode()

# Función para agregar una nueva contraseña a la base de datos
def add_password(service, username, password):
    try:
        encrypted_password = encrypt_password(password)
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO passwords (service, username, password) VALUES (?, ?, ?)", 
                       (service, username, encrypted_password))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al agregar la contraseña: {e}")
    finally:
        conn.close()

# Función para ver todas las contraseñas guardadas
def view_passwords():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT service, username, password FROM passwords")
        records = cursor.fetchall()
        return [(service, username, decrypt_password(password)) for service, username, password in records]
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al recuperar las contraseñas: {e}")
        return []
    finally:
        conn.close()

# Función para cambiar una contraseña existente
def change_password(service, new_password):
    try:
        encrypted_password = encrypt_password(new_password)
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE passwords SET password = ? WHERE service = ?", (encrypted_password, service))
        conn.commit()
        if cursor.rowcount == 0:
            messagebox.showwarning("Advertencia", "Servicio no encontrado")
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al cambiar la contraseña: {e}")
    finally:
        conn.close()

# Función para eliminar una contraseña por servicio
def delete_password(service):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM passwords WHERE service = ?", (service,))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al eliminar la contraseña: {e}")
    finally:
        conn.close()

# Función para establecer la contraseña maestra
def set_master_password(password):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT)")
        cursor.execute("DELETE FROM settings")  # Borrar la contraseña anterior si existe
        cursor.execute("INSERT INTO settings (key) VALUES (?)", (encrypt_password(password),))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al establecer la contraseña maestra: {e}")
    finally:
        conn.close()

# Función para obtener la contraseña maestra
def get_master_password():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT)")
        cursor.execute("SELECT key FROM settings")
        record = cursor.fetchone()
        return decrypt_password(record[0]) if record else None
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al obtener la contraseña maestra: {e}")
        return None
    finally:
        conn.close()

# Función para verificar la contraseña maestra
def check_master_password(master_password):
    stored_password = get_master_password()
    return stored_password == master_password


# Ventana para eliminar contraseña
def show_delete_password_window():
    delete_window = tk.Toplevel(main_window)
    delete_window.title("Eliminar Contraseña")

    tk.Label(delete_window, text="Ingresa el nombre del servicio:").pack(pady=10)
    service_entry = tk.Entry(delete_window)
    service_entry.pack(pady=10)

    def delete_service_password():
        service = service_entry.get()
        if service:
            delete_password(service)
            messagebox.showinfo("Éxito", "Contraseña eliminada con éxito")
            delete_window.destroy()
        else:
            messagebox.showwarning("Advertencia", "Por favor ingresa un nombre de servicio")

    tk.Button(delete_window, text="Eliminar", command=delete_service_password).pack(pady=10)


# Función para cambiar la contraseña de un servicio
def show_change_password_service_window():
    change_service_window = tk.Toplevel(main_window)
    change_service_window.title("Cambiar Contraseña")

    tk.Label(change_service_window, text="Ingresa el nombre del servicio:").pack(pady=10)
    service_entry = tk.Entry(change_service_window)
    service_entry.pack(pady=10)

    tk.Label(change_service_window, text="Ingresa la nueva contraseña:").pack(pady=10)
    new_password_entry = tk.Entry(change_service_window, show="*")
    new_password_entry.pack(pady=10)

    def change_service_password():
        service = service_entry.get()
        new_password = new_password_entry.get()
        if service and new_password:
            change_password(service, new_password)
            messagebox.showinfo("Éxito", "Contraseña cambiada con éxito")
            change_service_window.destroy()
        else:
            messagebox.showwarning("Advertencia", "Por favor completa todos los campos")

    tk.Button(change_service_window, text="Cambiar", command=change_service_password).pack(pady=10)


# Ventana para configurar la contraseña maestra
def show_setup_window():
    setup_window = tk.Toplevel(root)
    setup_window.title("Configuración de Contraseña Maestra")

    tk.Label(setup_window, text="Ingresa la contraseña maestra:").pack(pady=10)
    password_entry = tk.Entry(setup_window, show="*")
    password_entry.pack(pady=10)

    def save_password():
        password = password_entry.get()
        if password:
            set_master_password(password)
            setup_window.destroy()
            
        else:
            messagebox.showwarning("Advertencia", "Por favor ingresa una contraseña")

    tk.Button(setup_window, text="Guardar", command=save_password).pack(pady=10)

# Función para mostrar la ventana de inicio de sesión
def show_login_window():
    global master_password_entry  # Declarar como global aquí
    global login_window  # Asegúrate de que esta variable sea global
    login_window = tk.Toplevel(root)
    login_window.title("Iniciar Sesión")

    tk.Label(login_window, text="Contraseña:").pack()
    master_password_entry = tk.Entry(login_window, show="*")  # Define aquí la variable
    master_password_entry.pack()

    # Botón para verificar la contraseña
    tk.Button(login_window, text="Iniciar Sesión", command=verify_password).pack()

# Función para verificar la contraseña ingresada
def verify_password():
    if check_master_password(master_password_entry.get()):  # Accede a la variable global
        login_window.destroy()  # Cierra la ventana de inicio de sesión
        launch_main_window()     # Abre la ventana principal
    else:
        messagebox.showerror("Error", "Contraseña incorrecta")

# Ventana para cambiar la contraseña maestra
def show_change_password_window():
    change_window = tk.Toplevel(root)
    change_window.title("Cambiar Contraseña Maestra")

    tk.Label(change_window, text="Nueva contraseña maestra:").pack(pady=10)
    new_password_entry = tk.Entry(change_window, show="*")
    new_password_entry.pack(pady=10)

    def change_password():
        new_password = new_password_entry.get()
        if new_password:
            set_master_password(new_password)
            change_window.destroy()
            messagebox.showinfo("Éxito", "Contraseña maestra cambiada con éxito")
        else:
            messagebox.showwarning("Advertencia", "Por favor ingresa una nueva contraseña")

    tk.Button(change_window, text="Cambiar", command=change_password).pack(pady=10)

# Función principal de la aplicación
def main_app():
    global root
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal al inicio
    
    # Mostrar la ventana de configuración o inicio de sesión
    if get_master_password() is None:
        show_setup_window()  # Configura la contraseña maestra
    else:
        show_login_window()  # Muestra la ventana de inicio de sesión

    root.mainloop()  # Solo aquí se llama a mainloop

# Función que se llama después de un inicio de sesión exitoso
def launch_main_window():
    global main_window
    main_window = tk.Toplevel(root)
    main_window.title("Gestor de Contraseñas")

   # Configuración de la ventana principal
    tk.Label(main_window, text="Servicio:").grid(row=0, column=0, pady=(10, 5), sticky='e')
    tk.Label(main_window, text="Usuario:").grid(row=1, column=0, pady=(5, 5), sticky='e')
    tk.Label(main_window, text="Contraseña:").grid(row=2, column=0, pady=(5, 10), sticky='e')

    service_entry = tk.Entry(main_window)
    username_entry = tk.Entry(main_window)
    password_entry = tk.Entry(main_window, show='*')  # Mostrar asteriscos en la entrada de la contraseña
    service_entry.grid(row=0, column=1, padx=(5, 10), pady=(10, 5))
    username_entry.grid(row=1, column=1, padx=(5, 10), pady=(5, 5))
    password_entry.grid(row=2, column=1, padx=(5, 10), pady=(5, 10))

    # Función para manejar la adición de contraseñas desde la interfaz
    def handle_add_password():
        service = service_entry.get()
        username = username_entry.get()
        password = password_entry.get()
        if service and username and password:
            add_password(service, username, password)
            messagebox.showinfo("Éxito", "Contraseña añadida con éxito")
            service_entry.delete(0, tk.END)
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Advertencia", "Por favor completa todos los campos")

    # Función para mostrar las contraseñas guardadas en una nueva ventana
    def handle_view_passwords():
        passwords = view_passwords()
        if passwords:
            view_window = tk.Toplevel(main_window)
            view_window.title("Contraseñas Guardadas")
            for idx, (service, username, password) in enumerate(passwords):
                tk.Label(view_window, text=f"Servicio: {service}, Usuario: {username}, Contraseña: {password}").pack()
        else:
            messagebox.showinfo("Sin Contraseñas", "No hay contraseñas guardadas")

   # Botón para agregar una nueva contraseña
    tk.Button(main_window, text="Añadir Contraseña", command=handle_add_password).grid(row=3, column=0, pady=10, columnspan=2)

    # Botón para ver contraseñas
    tk.Button(main_window, text="Ver Contraseñas", command=handle_view_passwords).grid(row=4, column=0, pady=10, columnspan=2)

    # Botón para eliminar una contraseña
    tk.Button(main_window, text="Eliminar Contraseña", command=show_delete_password_window).grid(row=5, column=0, pady=10, columnspan=2)

    # Botón para cambiar la contraseña de servicio
    tk.Button(main_window, text="Cambiar Contraseña de Servicio", command=show_change_password_service_window).grid(row=6, column=0, pady=10, columnspan=2)

    # Botón para cambiar la contraseña maestra
    tk.Button(main_window, text="Cambiar Contraseña Maestra", command=show_change_password_window).grid(row=7, column=0, pady=10, columnspan=2)

# Ejecutar la aplicación
if __name__ == "__main__":
    main_app()
