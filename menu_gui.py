import tkinter as tk
import subprocess
import os
import signal
import psutil
import sqlite3
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

# Variable global para el proceso de la cámara
camera_process = None

def start_camera():
    """Inicia el contador de personas abriendo la cámara."""
    global camera_process
    if camera_process is None:
        try:
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
    """Muestra una ventana con opciones de gráficas para las estadísticas."""

    def open_graph_window(graph_type):
        """Abre una ventana con la gráfica seleccionada que se actualiza en tiempo real."""
        graph_window = tk.Toplevel(root)
        graph_window.title(f"Gráfica - {graph_type.capitalize()}")
        graph_window.geometry("700x500")

        # Configurar la gráfica
        fig, ax = plt.subplots(figsize=(6, 4))
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        def update_graph():
            """Actualiza la gráfica en tiempo real según el tipo."""
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
                if graph_type == "line":
                    ax.plot(x, y_entries, label="Entradas", color="blue")
                    ax.plot(x, y_exits, label="Salidas", color="red")
                    ax.set_title("Gráfico Lineal")
                elif graph_type == "bar":
                    bar_width = 0.4
                    x_indices = np.arange(len(x))
                    ax.bar(x_indices - bar_width / 2, y_entries, bar_width, label="Entradas", color="blue")
                    ax.bar(x_indices + bar_width / 2, y_exits, bar_width, label="Salidas", color="red")
                    ax.set_xticks(x_indices)
                    ax.set_xticklabels(x, rotation=45)
                    ax.set_title("Gráfico de Barras")
                elif graph_type == "hist":
                    ax.hist([y_entries, y_exits], bins=5, label=["Entradas", "Salidas"], color=["blue", "red"], alpha=0.7)
                    ax.set_title("Histograma")
                elif graph_type == "pie":
                    total_entries = sum(y_entries)
                    total_exits = sum(y_exits)
                    ax.pie([total_entries, total_exits], labels=["Entradas", "Salidas"], autopct='%1.1f%%', colors=["blue", "red"])
                    ax.set_title("Gráfico de Pastel")

                ax.legend()
                canvas.draw()
                conn.close()
            except sqlite3.Error as e:
                print(f"Error al leer la base de datos: {e}")
            graph_window.after(2000, update_graph)

        # Iniciar la actualización de la gráfica
        update_graph()

    # Crear la ventana para seleccionar el tipo de gráfica
    stats_window = tk.Toplevel(root)
    stats_window.title("Opciones de Gráficas")
    stats_window.geometry("300x200")

    tk.Label(stats_window, text="Seleccione el tipo de gráfica", font=("Helvetica", 12)).pack(pady=10)

    # Botones para cada tipo de gráfica
    tk.Button(stats_window, text="Gráfico Lineal", command=lambda: open_graph_window("line"), font=("Helvetica", 10)).pack(pady=5)
    tk.Button(stats_window, text="Gráfico de Barras", command=lambda: open_graph_window("bar"), font=("Helvetica", 10)).pack(pady=5)
    tk.Button(stats_window, text="Histograma", command=lambda: open_graph_window("hist"), font=("Helvetica", 10)).pack(pady=5)
    tk.Button(stats_window, text="Gráfico de Pastel", command=lambda: open_graph_window("pie"), font=("Helvetica", 10)).pack(pady=5)

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
