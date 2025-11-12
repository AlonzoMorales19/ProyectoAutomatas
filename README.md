# Analizador de Expresiones Regulares y Autómatas

Este proyecto es una aplicación web que permite analizar expresiones regulares, construir su árbol, generar el Autómata Finito Determinista (AFD) y el Autómata Finito No Determinista (AFN) correspondientes y validar sus respectivas cadenas.

# Características

*   **Interfaz de Usuario Intuitiva:** Una interfaz sencilla para ingresar expresiones regulares y cadenas, y visualizar los resultados.
*   **Análisis de Expresiones Regulares:** Procesa expresiones regulares para construir su árbol.
*   **Visualización Interactiva:** Utiliza la librería `vis-network` para mostrar de forma gráfica e interactiva el árbol, el AFD y el AFN.
*   **Tablas de Transición y Siguiente Posición:** Genera y muestra las tablas de transición y la de siguiente posición del árbol.
*   **Generación de AFD y AFN:** A partir de la tabla de siguiente posición, se construyen y visualizan los AFD y AFN.
*   **Validación de Cadenas:** Permite ingresar múltiples cadenas de texto para verificar si son válidas según la expresión regular analizada.

# Estructura del Proyecto

El proyecto consta de dos partes principales:

1.  **Backend (Python con Flask):** `proyecto.py`
    *   Contiene la lógica para el análisis de expresiones regulares, la construcción del árbol, la generación del AFD/AFN y la simulación de cadenas.
    *   Expone una API REST (`/analizar`) para que el frontend interactúe con la lógica del autómata.
2.  **Frontend (HTML, CSS, JavaScript):** `visual.html`
    *   Proporciona la interfaz de usuario.
    *   Envía las expresiones regulares y cadenas al backend.
    *   Recibe los datos del backend y los visualiza utilizando `vis-network` y tablas HTML.

# Requisitos

* Python 3.x
* `pip` (administrador de paquetes de Python)

# Instalación

Sigue estos pasos para configurar y ejecutar el proyecto localmente:

1.  **Clona el repositorio** (o descarga los archivos `proyecto.py` y `visual.html` en una misma carpeta).

2.  **Instala las dependencias de Python:**
    Abre una terminal en la carpeta del proyecto y ejecuta:
    ```bash
    pip install Flask Flask-Cors
    ```

# Sintaxis de Expresiones Regulares

El analizador utiliza la siguiente sintaxis:

* **Unión (+ = |):** `|` (Ej: `a|b`)
* **Concatenación:** Implícita. Escribir dos símbolos juntos significa concatenación (Ej: `ab` significa 'a' seguida de 'b').
* **Cierre de Kleene (Estrella):** `*` (Ej: `a*` significa cero o más 'a')
* **Agrupación:** `()` (Ej: `(a|b)*`)
* **Literales:** Cualquier carácter que no sea un operador (`|`, `*`, `(`, `)`), como `a`, `B`, `9`, o incluso `.`, se trata como un símbolo literal del alfabeto.

# Uso

1.  **Inicia el servidor backend:**
    Desde la terminal en la carpeta del proyecto, ejecuta:
    ```bash
    python proyecto.py
    ```
    Verás un mensaje indicando que el servidor ha iniciado en `http://127.0.0.1:5000`. **No cierres esta terminal.**

2.  **Abre la interfaz de usuario:**
    Busca el archivo `visual.html` en tu carpeta y ábrelo directamente en tu navegador web. **simplemente haz doble clic sobre él**

3.  **Analiza y Valida:**
    * En el campo "1. Ingrese la Expresión Regular", escribe la expresión regular que deseas analizar.
    * Haz clic en el botón "Construir" para generar el árbol, las tablas y los diagramas del AFD y AFN.

    * En el campo "2. Ingrese Cadenas a Validar", escribe las cadenas que deseas probar (una por línea).
    * Haz clic en el botón "Validar" para ver los resultados.