#main.py
from modules.analisis import analizar_expedientes

if __name__ == "__main__":
    RUTA_CARPETA = r"C:\Users\abouvier\Downloads\Digitalizacion_jubilaciones"
    analizar_expedientes(RUTA_CARPETA)
