import os
import tkinter as tk
from tkinter import filedialog, messagebox
from urllib.parse import urlparse
import customtkinter as ctk
import yt_dlp
from googleapiclient.discovery import build
from PIL import Image
import requests
import io
from pytube import YouTube
import vlc

# Clave de API de YouTube (reemplaza con la tuya)
API_KEY = 'TU_API_YOUTUBE_AQUI'


def es_url_valida(url):
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc]) and "youtube.com" in parsed_url.netloc


def descargar_mp3(url, ruta_descarga):
    try:
        if not es_url_valida(url):
            raise ValueError("La URL proporcionada no es válida.")

        carpeta_descarga = os.path.join(ruta_descarga, "Musica GD")
        if not os.path.exists(carpeta_descarga):
            os.makedirs(carpeta_descarga)

        opciones_ydl = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(carpeta_descarga, '%(title)s.%(ext)s'),
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(opciones_ydl) as ydl:
            ydl.download([url])

        messagebox.showinfo("Descarga completa", "Descarga finalizada con éxito en la carpeta 'Musica GD'")
    except ValueError as ve:
        messagebox.showerror("Error en la URL", str(ve))
    except Exception as e:
        messagebox.showerror("Error inesperado", f"Error al descargar: {e}")


def seleccionar_carpeta(var_carpeta):
    carpeta_seleccionada = filedialog.askdirectory()
    if carpeta_seleccionada:
        var_carpeta.set(carpeta_seleccionada)


def buscar_youtube(consulta):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    solicitud = youtube.search().list(part="snippet", maxResults=10, q=consulta, type="video")
    respuesta = solicitud.execute()

    resultados_video = []
    for item in respuesta['items']:
        titulo = item['snippet']['title']
        id_video = item['id']['videoId']
        url_miniatura = item['snippet']['thumbnails']['high']['url']
        resultados_video.append((titulo, f"https://www.youtube.com/watch?v={id_video}", url_miniatura))

    return resultados_video


def obtener_imagen_miniatura(url_miniatura):
    try:
        respuesta = requests.get(url_miniatura)
        respuesta.raise_for_status()

        if 'image' not in respuesta.headers.get('Content-Type', ''):
            raise ValueError("La URL no devuelve una imagen.")

        datos_imagen = Image.open(io.BytesIO(respuesta.content))
        datos_imagen = datos_imagen.resize((320, 180), Image.LANCZOS)
        return ctk.CTkImage(light_image=datos_imagen, dark_image=datos_imagen, size=(320, 180))

    except Exception as e:
        print(f"Error al obtener la miniatura: {e}")
        return None


def al_seleccionar_video(url, entrada_url):
    entrada_url.delete(0, tk.END)
    entrada_url.insert(0, url)


def obtener_mejor_url_stream(url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url']


def toggle_reproduccion():
    global player
    if player:
        if player.is_playing():
            player.pause()
        else:
            player.play()

def reproducir_preview(url, marco_video):
    global player
    try:
        # Limpiar el marco de video
        for widget in marco_video.winfo_children():
            widget.destroy()

        # Obtener la URL del stream usando yt_dlp
        playurl = obtener_mejor_url_stream(url)

        # Crear una instancia de VLC y un reproductor de medios
        instance = vlc.Instance()
        player = instance.media_player_new()
        media = instance.media_new(playurl)
        player.set_media(media)

        # Crear un marco para el video
        frame = tk.Frame(marco_video, bg="black")
        frame.pack(expand=True, fill="both")

        # En sistemas Windows, necesitamos el identificador de la ventana
        if os.name == "nt":
            player.set_hwnd(frame.winfo_id())
        else:  # En sistemas Unix
            player.set_xwindow(frame.winfo_id())

        # Crear botón de pausa/reproducción
        boton_pausa = ctk.CTkButton(marco_video, text="Pausar/Reproducir", command=toggle_reproduccion)
        boton_pausa.pack(pady=10)

        # Reproducir el video
        player.play()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo reproducir la vista previa: {e}")

def buscar_y_mostrar_resultados(var_busqueda, marco_resultados, entrada_url, marco_video):
    consulta = var_busqueda.get()
    for widget in marco_resultados.winfo_children():
        widget.destroy()
    if consulta:
        resultados = buscar_youtube(consulta)
        for titulo, url, url_miniatura in resultados:
            marco_item_resultado = ctk.CTkFrame(marco_resultados, corner_radius=10, fg_color="transparent")
            marco_item_resultado.pack(fill="x", padx=10, pady=10)

            imagen_miniatura = obtener_imagen_miniatura(url_miniatura)

            if imagen_miniatura:
                etiqueta_miniatura = ctk.CTkLabel(marco_item_resultado, image=imagen_miniatura, text="")
                etiqueta_miniatura.image = imagen_miniatura
                etiqueta_miniatura.pack(side="left", padx=10)

            marco_info = ctk.CTkFrame(marco_item_resultado, corner_radius=10, fg_color="transparent")
            marco_info.pack(side="left", fill="x", expand=True, padx=10)

            etiqueta_titulo = ctk.CTkLabel(marco_info, text=titulo, wraplength=350, justify="left", anchor="w")
            etiqueta_titulo.pack(fill="x", pady=5)

            marco_botones = ctk.CTkFrame(marco_info, corner_radius=10, fg_color="transparent")
            marco_botones.pack(fill="x")

            boton_seleccionar = ctk.CTkButton(marco_botones, text="Seleccionar",
                                              command=lambda u=url: al_seleccionar_video(u, entrada_url),
                                              width=100)
            boton_seleccionar.pack(side="left", padx=(0, 10))

            boton_preview = ctk.CTkButton(marco_botones, text="Vista Previa",
                                          command=lambda u=url: reproducir_preview(u, marco_video),
                                          width=100)
            boton_preview.pack(side="left")


def crear_gui():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Descargador de MP3 de YouTube")
    root.geometry("1200x800")

    # Frame principal
    marco_principal = ctk.CTkFrame(root)
    marco_principal.pack(fill="both", expand=True, padx=20, pady=20)

    # Frame de búsqueda
    marco_busqueda = ctk.CTkFrame(marco_principal)
    marco_busqueda.pack(fill="x", padx=10, pady=10)

    var_busqueda = tk.StringVar()
    entrada_busqueda = ctk.CTkEntry(marco_busqueda, textvariable=var_busqueda, width=400,
                                    placeholder_text="Buscar video...")
    entrada_busqueda.pack(side="left", padx=(0, 10))

    # Frame para resultados y vista previa
    marco_contenido = ctk.CTkFrame(marco_principal)
    marco_contenido.pack(fill="both", expand=True, padx=10, pady=10)

    # Frame de resultados (izquierda)
    marco_resultados = ctk.CTkScrollableFrame(marco_contenido, corner_radius=10, width=600, height=500)
    marco_resultados.pack(side="left", fill="both", expand=True, padx=(0, 10))

    # Frame de vista previa (derecha)
    marco_video = ctk.CTkFrame(marco_contenido, corner_radius=10, width=560, height=315)
    marco_video.pack(side="right", fill="both", expand=True)

    boton_buscar = ctk.CTkButton(marco_busqueda, text="Buscar",
                                 command=lambda: buscar_y_mostrar_resultados(var_busqueda, marco_resultados,
                                                                             entrada_url, marco_video))
    boton_buscar.pack(side="left")

    # Frame de descarga
    marco_descarga = ctk.CTkFrame(marco_principal)
    marco_descarga.pack(fill="x", padx=10, pady=10)

    entrada_url = ctk.CTkEntry(marco_descarga, width=400, placeholder_text="URL del video seleccionado")
    entrada_url.pack(side="left", padx=(0, 10))

    var_carpeta = tk.StringVar(value=os.path.expanduser("~"))
    boton_carpeta = ctk.CTkButton(marco_descarga, text="Seleccionar carpeta",
                                  command=lambda: seleccionar_carpeta(var_carpeta))
    boton_carpeta.pack(side="left", padx=(0, 10))

    boton_descargar = ctk.CTkButton(marco_descarga, text="Descargar MP3",
                                    command=lambda: descargar_mp3(entrada_url.get(), var_carpeta.get()))
    boton_descargar.pack(side="left")

    root.mainloop()


if __name__ == "__main__":
    crear_gui()
