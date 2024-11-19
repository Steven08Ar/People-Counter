import tkinter as tk
import subprocess
import os
import signal
import psutil
import sqlite3
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import time

# Variable global para el proceso de la cámara
camera_process = None

def start_camera():
    """Inicia el contador de personas abriendo la cámara."""
    global camera_process
    if camera_process is None:
        try:
            # Ejecuta el comando para iniciar la cámara
            camera_process = subprocess.Popen([
                "python", "people_counter.py",
                "--prototxt", "detector/MobileNetSSD_deploy.prototxt",
                "--model", "detector/MobileNetSSD_deploy.caffemodel"
            ])
            status_label.config(text="Cámara activada")
        except Exception as e:
            status_label.config(text=f"Error al iniciar: {e}")
    else:
        status_label.config(text="La cámara ya está activa")

def stop_camera():
    """Detiene el proceso de la cámara."""
    global camera_process
    if camera_process is not None:
        try:
            # Finaliza el proceso del contador de personas
            process = psutil.Process(camera_process.pid)
            for proc in process.children(recursive=True):
                proc.terminate()
            process.terminate()
            camera_process = None
            status_label.config(text="Cámara desactivada")
        except Exception as e:
            status_label.config(text=f"Error al detener: {e}")
    else:
        status_label.config(text="La cámara no está activa")

def show_statistics():
    """Abre dos ventanas: una tabla y una gráfica lineal que se actualizan automáticamente."""

    def update_table():
        """Actualiza la tabla con datos de la base de datos."""
        for row in tree.get_children():
            tree.delete(row)
        try:
            conn = sqlite3.connect("people_count.db")
            cursor = conn.cursor()
            cursor.execute("SELECT datetime, entries, exits FROM statistics ORDER BY id DESC LIMIT 10")
            rows = cursor.fetchall()
            for row in rows:
                tree.insert("", "end", values=row)
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al leer la base de datos: {e}")
        # Reprogramar la actualización en 2 segundos
        stats_window.after(2000, update_table)

    def update_graph():
        """Actualiza la gráfica con datos de la base de datos."""
        try:
            conn = sqlite3.connect("people_count.db")
            cursor = conn.cursor()
            cursor.execute("SELECT datetime, entries, exits FROM statistics ORDER BY id DESC LIMIT 10")
            rows = cursor.fetchall()
            rows.reverse()  # Ordenar por fecha ascendente
            x = [row[0] for row in rows]
            y_entries = [row[1] for row in rows]
            y_exits = [row[2] for row in rows]

            ax.clear()
            ax.plot(x, y_entries, label="Entradas", color="blue")
            ax.plot(x, y_exits, label="Salidas", color="red")
            ax.set_title("Estadísticas en Tiempo Real")
            ax.set_xlabel("Fecha y Hora")
            ax.set_ylabel("Conteo")
            ax.legend()
            canvas.draw()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al leer la base de datos: {e}")
        # Reprogramar la actualización en 2 segundos
        graph_window.after(2000, update_graph)

    # Crear la ventana para la tabla
    stats_window = tk.Toplevel(root)
    stats_window.title("Estadísticas - Tabla")
    stats_window.geometry("500x300")

    columns = ("datetime", "entries", "exits")
    tree = ttk.Treeview(stats_window, columns=columns, show="headings")
    tree.heading("datetime", text="Fecha y Hora")
    tree.heading("entries", text="Entradas")
    tree.heading("exits", text="Salidas")
    tree.pack(fill=tk.BOTH, expand=True)

    # Actualizar tabla inicialmente
    update_table()

    # Crear la ventana para la gráfica
    graph_window = tk.Toplevel(root)
    graph_window.title("Estadísticas - Gráfica")
    graph_window.geometry("600x400")

    # Configurar la gráfica
    fig, ax = plt.subplots(figsize=(6, 4))
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Actualizar gráfica inicialmente
    update_graph()

def close_application():
    """Cierra la interfaz y termina la aplicación."""
    stop_camera()  # Detener la cámara si está activa
    root.destroy()

# Crear la ventana principal
root = tk.Tk()
root.title("Menú - Contador de Personas")
root.geometry("400x300")

# Etiqueta de título
title_label = tk.Label(root, text="Contador de Personas", font=("Helvetica", 16))
title_label.pack(pady=10)

# Botón para iniciar la cámara
start_button = tk.Button(root, text="Activar Cámara", command=start_camera, font=("Helvetica", 12), bg="green", fg="white")
start_button.pack(pady=10)

# Botón para apagar la cámara
stop_button = tk.Button(root, text="Apagar Cámara", command=stop_camera, font=("Helvetica", 12), bg="red", fg="white")
stop_button.pack(pady=10)

# Botón para ver estadísticas
stats_button = tk.Button(root, text="Ver Estadísticas", command=show_statistics, font=("Helvetica", 12), bg="blue", fg="white")
stats_button.pack(pady=10)

# Botón para cerrar la aplicación
close_button = tk.Button(root, text="Cerrar Aplicación", command=close_application, font=("Helvetica", 12), bg="gray", fg="white")
close_button.pack(pady=10)

# Etiqueta para mostrar el estado de la cámara
status_label = tk.Label(root, text="Estado: Inactivo", font=("Helvetica", 10))
status_label.pack(pady=20)

# Ejecutar el bucle principal de la interfaz
root.mainloop()
