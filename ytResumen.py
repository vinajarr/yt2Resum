import os
import subprocess
import argparse
from faster_whisper import WhisperModel
from groq import Groq


# Lista de idiomas soportados por Whisper
LANGUAGES = {
    "auto": "Detección automática",
    "af": "Afrikáans", "sq": "Albanés", "am": "Amárico", "ar": "Árabe", "hy": "Armenio", "as": "Asamés",
    "az": "Azerbaiyano", "bn": "Bengalí", "bs": "Bosnio", "bg": "Búlgaro", "ca": "Catalán", "zh": "Chino",
    "hr": "Croata", "cs": "Checo", "da": "Danés", "nl": "Neerlandés", "en": "Inglés", "eo": "Esperanto",
    "et": "Estonio", "fi": "Finés", "fr": "Francés", "gl": "Gallego", "ka": "Georgiano", "de": "Alemán",
    "el": "Griego", "gu": "Gujarati", "he": "Hebreo", "hi": "Hindi", "hu": "Húngaro", "is": "Islandés",
    "id": "Indonesio", "ga": "Irlandés", "it": "Italiano", "ja": "Japonés", "jv": "Javanés", "kn": "Canarés",
    "kk": "Kazajo", "km": "Jemer", "ko": "Coreano", "lo": "Lao", "lv": "Letón", "lt": "Lituano", "mk": "Macedonio",
    "ms": "Malayo", "ml": "Malayalam", "mt": "Maltés", "mr": "Maratí", "mn": "Mongol", "ne": "Nepalí",
    "no": "Noruego", "fa": "Persa", "pl": "Polaco", "pt": "Portugués", "pa": "Punyabí", "ro": "Rumano",
    "ru": "Ruso", "sr": "Serbio", "si": "Cingalés", "sk": "Eslovaco", "sl": "Esloveno", "es": "Español",
    "sw": "Swahili", "sv": "Sueco", "tl": "Tagalo", "ta": "Tamil", "te": "Telugu", "th": "Tailandés",
    "tr": "Turco", "uk": "Ucraniano", "ur": "Urdu", "uz": "Uzbeko", "vi": "Vietnamita", "cy": "Galés"
}



def dividir_en_fragmentos(texto, max_palabras=5800):
    """Devuelve una lista de fragmentos de texto, cada uno con un máximo de max_palabras."""
    palabras = texto.split()
    fragmentos = []
    for i in range(0, len(palabras), max_palabras):
        fragmento = " ".join(palabras[i:i+max_palabras])
        fragmentos.append(fragmento)
    return fragmentos

def resumir_con_groq(texto):
    """Hace una petición a Groq para resumir el texto en español."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt_usuario = f"Resume el siguiente texto en español:\n\n{texto}"
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt_usuario}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def resumen_multipasos(texto, max_palabras=5800):
    """
    Repite el proceso de resumir en fragmentos y unirlos,
    hasta que el texto quede por debajo de max_palabras.
    """
    while len(texto.split()) > max_palabras:
        # 1. Dividir texto largo
        fragmentos = dividir_en_fragmentos(texto, max_palabras)
        # 2. Resumir cada fragmento
        resumenes_parciales = [resumir_con_groq(frag) for frag in fragmentos]
        # 3. Unir los resúmenes parciales
        texto = "\n".join(resumenes_parciales)
    # Al final, hacer un último resumen del texto final
    return resumir_con_groq(texto)

def resumir_texto_archivo(ruta_entrada, ruta_salida, max_palabras=4000):
    """Lee un archivo, lo resume en varias pasadas si es muy largo y guarda el resultado."""
    # 1. Cargar texto
    with open(ruta_entrada, "r", encoding="utf-8") as f:
        texto = f.read()

    # 2. Resumir con múltiple pasadas si excede el límite
    resumen_final = resumen_multipasos(texto, max_palabras)

    # 3. Guardar el resumen final en el archivo de salida
    with open(ruta_salida, "w", encoding="utf-8") as out:
        out.write(resumen_final)

    print(f"Resumen guardado en: {ruta_salida}")



def convert_audio(input_file, output_file="converted_audio.wav"):
    """
    Convierte cualquier archivo de audio o video a formato mono y 16kHz usando FFmpeg.
    """
    command = [
        "ffmpeg", "-y",  # -y sobrescribe el archivo si existe
        "-i", input_file,  # Archivo de entrada
        "-ac", "1",  # Convertir a mono
        "-ar", "16000",  # Frecuencia de muestreo a 16kHz
        output_file  # Archivo de salida
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_file
    except subprocess.CalledProcessError as e:
        print("❌ Error en la conversión con FFmpeg:", e)
        return None

def transcribe_audio(input_file, output_txt, language="es"):
    """
    Transcribe el audio convertido, permitiendo seleccionar el idioma.
    Guarda la transcripción en un archivo .txt.
    """
    model = WhisperModel("base", compute_type="int8")  # Optimizado para M3 Pro

    # Convertir el archivo si es necesario
    converted_file = convert_audio(input_file)
    if not converted_file:
        print("❌ No se pudo convertir el archivo de audio/video.")
        return
    
    print(f"🔊 Transcribiendo en idioma: {LANGUAGES.get(language, 'Desconocido')}...")

    # Transcripción con el idioma seleccionado (o automático si es 'auto')
    segments, _ = model.transcribe(converted_file, language=None if language == "auto" else language)
    
    # Unir segmentos de la transcripción
    transcription = " ".join(segment.text for segment in segments)

    # Guardar la transcripción en el archivo de salida
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(transcription)
    
    print(f"✅ Transcripción guardada en: {output_txt}")

def show_help():
    """Muestra el menú de ayuda."""
    print("\n📝 Uso del script:")
    print("   python3 whisper_transcriber.py <archivo_entrada> <archivo_salida.txt> [idioma]\n")
    print("📌 Parámetros:")
    print("   <archivo_entrada>  → Ruta del archivo de audio o video a transcribir.")
    print("   <archivo_salida.txt> → Ruta donde guardar la transcripción.")
    print("   [idioma] (opcional) → Código del idioma (ejemplo: 'es' para español, 'en' para inglés).")
    print("                          Usa 'auto' para detección automática.")
    print("\n🌍 Idiomas disponibles:")
    for code, name in LANGUAGES.items():
        print(f"   {code}: {name}")
    print("\n🔹 Ejemplo de uso:")
    print("   python3 whisper_transcriber.py video.mp4 transcripcion.txt es")
    print("   python3 whisper_transcriber.py audio.mp3 resultado.txt auto\n")
    exit()

def descargar_audio_mp3(url, carpeta_descarga="."):
    try:
        # Prepara el comando para descargar como MP3
        comando = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", "./audio.mp3",
            url
        ]
        subprocess.run(comando, check=True)
        print("Descarga completada.")
    except subprocess.CalledProcessError as e:
        print("Error al ejecutar yt-dlp:", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descargar audio de YouTube como MP3 usando yt-dlp.")
    parser.add_argument("url", help="URL del video de YouTube")
    parser.add_argument("-l", "-language", default="es", help="Código del idioma (por defecto: español). Usa 'auto' para detección automática.")
    parser.add_argument("-o", "-output", default="/Users/victor/Downloads", help="Carpeta de destino")
    parser.add_argument("-help", action="store_true", help="Muestra el menú de ayuda.")
    args = parser.parse_args()

    if args.help:
        show_help()
    elif not args.url:
        print("❌ Error: Debes ingresar la URL del video de YouTube.")
        show_help()
     # Validar idioma
    elif args.language not in LANGUAGES:
        print(f"❌ Error: Idioma '{args.language}' no es válido.")
        show_help()
    else:
        descargar_audio_mp3(args.url, args.output)
        transcribe_audio("./audio.mp3", "./transcripcion.txt", args.language)
        os.remove("./audio.mp3")
        os.remove("./converted_audio.wav")
        print("Archivos de audio eliminado.")
        resumir_texto_archivo("./transcripcion.txt", args.output + "/resumen.txt")
        os.remove("./transcripcion.txt")
        print("Archivo de transcripción eliminado.")
        print("Proceso completado.")
        print("Resumen guardado en:", args.output + "/resumen.txt")



