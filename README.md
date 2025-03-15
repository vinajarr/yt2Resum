# yt2Resum
Script en python que permite automatizar la tarea de descargar audio de video en youtube -> transcribir el textos -> utilizar modelo LLM open resumir el texto

Es necesario crear tu propia API Key en: https://console.groq.com/keys y definarla como variable de entorno en tu sistema operativo

para ejecutar la scrip usa: 
python3 ytResumen.py <url> -l <lenguaje> -o <carpeta a guardar resumen.txt>

los campos  -l y -o son opcionales y pordecto usa:
<lenguaje> = "es" //español
<carpeta a guardar resumen.txt> = mi ruta a la carpeta de descargas 

python3 ytResumen.py <url> -l <lenguaje> -o <carpeta a guardar resumen.txt>
