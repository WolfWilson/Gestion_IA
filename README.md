# 🧠 GESTIÓN IA - Automatización de Control Documental Jubilatorio

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![PDF Analysis](https://img.shields.io/badge/PDF%20Parser-pdfplumber-orange?style=for-the-badge&logo=adobeacrobatreader)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-brightgreen?style=for-the-badge&logo=qt)
![Machine Learning](https://img.shields.io/badge/ML-Preparado-orange?style=for-the-badge&logo=pytorch)
![NLP](https://img.shields.io/badge/NLP-Futuro%20Integrado-green?style=for-the-badge&logo=openai)
![Windows](https://img.shields.io/badge/Windows-10%2B-lightgrey?style=for-the-badge&logo=windows)
![Estado](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/Licencia-MIT-blue?style=for-the-badge)

---

## 📢 Descripción General

**GESTIÓN IA** es una herramienta de asistencia inteligente para el análisis automatizado de **expedientes jubilatorios** en formato PDF. Su objetivo principal es validar, clasificar y detectar automáticamente la completitud documental en las etapas iniciales del trámite, evitando omisiones y reduciendo la carga de trabajo manual.

El sistema está pensado para operar sobre documentos escaneados o digitales, extrayendo datos clave como nombres, fechas, servicios prestados, tipos de cargos, etc., y validándolos en base a reglas definidas.

---

## 🚀 Objetivos del Proyecto

- 📄 Automatizar el análisis estructurado de documentos PDF.
- 📋 Detectar faltantes o errores comunes en la documentación.
- ✅ Validar la completitud e integridad de campos clave.
- ⏱️ Agilizar el proceso de admisión documental.
- 🧠 Preparar una segunda etapa para cómputo automático de servicios con IA (Machine Learning y NLP).

---

## 🧩 Características Destacadas

✔ Análisis por lotes o individual de PDFs  
✔ Validaciones configurables desde código  
✔ Registros detallados en archivos de log  
✔ Interfaz gráfica intuitiva con PyQt6  
✔ Modularidad lista para integración con IA y bases de datos  

---

## 🛠️ Tecnologías Utilizadas

| Categoría         | Herramientas                                                        |
|------------------|---------------------------------------------------------------------|
| Lenguaje         | `Python 3.12`                                                       |
| PDF Parsing      | `pdfplumber`, `PyPDF2`, `pdfminer.six`                             |
| GUI              | `PyQt6`                                                             |
| Procesamiento    | `pandas`, `openpyxl`                                                |
| Logging          | `loguru`, `logging`                                                 |
| Validaciones     | `pydantic`, `validators`                                            |
| NLP / IA (futuro)| `transformers`, `torch`, `spacy`, `sentence-transformers`          |

---

## 📦 Instalación y Uso

### 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/gestion_ia.git
cd gestion_ia
```

### 2️⃣ Crear entorno virtual
```bash
python -m venv venv
```
### 3️⃣ Activar entorno virtual
En Windows:
```bash
venv\Scripts\activate
```
### 4️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```
### 5️⃣ Ejecutar la aplicación
```bash
python main.py
```