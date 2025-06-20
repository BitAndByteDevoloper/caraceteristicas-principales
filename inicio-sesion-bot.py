import os
import time
import random
import logging
import chromedriver_autoinstaller
import pyautogui
import json
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# ---------------------------------------
# Carga de entorno y configuración de logging
# ---------------------------------------
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)

# ---------------------------------------
# Coordenadas fijas para el bypass
# ---------------------------------------
REFRESH_X, REFRESH_Y   = 98, 61     # Botón “X” / “Recargar”
CHECKBOX_X, CHECKBOX_Y = 531, 373   # Casilla “No soy un robot”

# ---------------------------------------
# Variables globales de control
# ---------------------------------------
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
CHECKBOX_IMG  = os.path.join(SCRIPT_DIR, 'checkbox.png')
FIRST_BYPASS  = True  # Solo hacer bypass una vez en login

# ---------------------------------------
# Movimiento “humano” del ratón
# ---------------------------------------
def human_like_slide_to(x, y):
    x0, y0 = pyautogui.position()
    steps = random.randint(10, 15)
    for i in range(steps):
        xi = x0 + (x - x0) * (i + 1) // steps
        yi = y0 + (y - y0) * (i + 1) // steps
        pyautogui.moveTo(xi, yi, duration=random.uniform(0.01, 0.03))
    pyautogui.moveTo(x, y, duration=random.uniform(0.02, 0.05))

# ---------------------------------------
# Clicks para sortear Cloudflare
# ---------------------------------------
def click_refresh():
    human_like_slide_to(REFRESH_X, REFRESH_Y)
    pyautogui.click()

def click_checkbox():
    if random.random() < 0.2:
        human_like_slide_to(CHECKBOX_X + 10, CHECKBOX_Y + 10)
        pyautogui.click()
        time.sleep(random.uniform(0.1, 0.3))
    human_like_slide_to(CHECKBOX_X, CHECKBOX_Y)
    pyautogui.click()

def is_checkbox_present():
    try:
        return pyautogui.locateOnScreen(CHECKBOX_IMG, confidence=0.8) is not None
    except:
        return False

# ---------------------------------------
# Bypass del challenge de Cloudflare
# ---------------------------------------
def bypass_cloudflare():
    global FIRST_BYPASS
    wait0 = 10 if FIRST_BYPASS else 5
    FIRST_BYPASS = False
    logging.info(f"Esperando {wait0}s antes de sortear Cloudflare")
    time.sleep(wait0)
    click_refresh()
    time.sleep(1)
    click_refresh()
    logging.info("Esperando 10s para que aparezca el checkbox")
    time.sleep(10)
    click_checkbox()
    time.sleep(random.uniform(10, 15))
    while is_checkbox_present():
        time.sleep(random.uniform(10, 15))
        click_checkbox()

# ---------------------------------------
# Configuración de Selenium
# ---------------------------------------
def setup_selenium():
    chromedriver_path = chromedriver_autoinstaller.install()
    opts = Options()
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--start-maximized")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.page_load_strategy = 'eager'
    opts.add_experimental_option("detach", True)
    logging.info("Iniciando ChromeDriver")
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=opts)
    driver.set_page_load_timeout(90)
    return driver

# ---------------------------------------
# Flujo principal
# ---------------------------------------
def main():
    # 1) Leer credenciales
    email = os.getenv("CT_EMAIL_CENTINELA")
    pwd   = os.getenv("CT_PASSWORD_CENTINELA")
    if not email or not pwd:
        logging.error("Faltan credenciales en .env")
        return

    driver = setup_selenium()

    # 2) Login (con bypass)
    driver.get("https://ctonline.mx/iniciar/correo")
    time.sleep(5)
    bypass_cloudflare()
    driver.get("https://ctonline.mx/iniciar/correo")
    time.sleep(3)

    try:
        wait = WebDriverWait(driver, 20)
        inp = wait.until(EC.presence_of_element_located((By.NAME, "correo")))
        inp.send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(pwd + Keys.RETURN)
        wait.until(EC.url_contains("ctonline.mx"))
        logging.info("Login completado")
    except TimeoutException:
        logging.error("Formulario de login no detectado")
        return  # NO cerramos el navegador

    # 3) Leer JSON y primer SKU
    json_path = os.path.join(SCRIPT_DIR, "coincidencias.json")
    logging.info(f"Cargando SKUs desde: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    sku = products[0].get("clave")
    logging.info(f"Primer SKU: {sku}")

    # Crear carpeta para este SKU
    descarga_dir = os.path.join(SCRIPT_DIR, "descarga-archivos", sku)
    os.makedirs(descarga_dir, exist_ok=True)

    # 4) Búsqueda del producto (SIN bypass)
    driver.get(f"https://ctonline.mx/buscar/productos?b={sku}")
    time.sleep(10)
    ct = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "ct-description"))
    )
    try:
        link = ct.find_element(By.CSS_SELECTOR, "h6 a").get_attribute("href")
    except:
        link = ct.find_element(By.CSS_SELECTOR, "h5 a").get_attribute("href")
    logging.info(f"Enlace encontrado: {link}")

    # 5) Abrir detalle en nueva pestaña y cambiar a ella
    driver.execute_script("window.open(arguments[0], '_blank');", link)
    driver.switch_to.window(driver.window_handles[-1])

    # 6) Esperar a que el panel se despliegue completamente
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#ct_technical.in"))
    )
    time.sleep(10)  # espera extra para garantía

    # 7) Guardar características como HTML
    panel = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "panel-body"))
    )
    features_html = panel.get_attribute("outerHTML")
    features_file = os.path.join(descarga_dir, f"{sku}_caracteristicas.html")
    with open(features_file, "w", encoding="utf-8") as f:
        f.write(features_html)
    print("Características guardadas en", features_file)

    # 8) Guardar información adicional (ficha técnica)
    info_container = driver.find_element(
        By.CSS_SELECTOR,
        "div.panel-body#ficha_tecnica > div.ct-section"
    )
    info_html = info_container.get_attribute("outerHTML")
    info_file = os.path.join(descarga_dir, f"{sku}_info_adicional.html")
    with open(info_file, "w", encoding="utf-8") as f:
        f.write(info_html)
    print("Información adicional guardada en", info_file)

    # 9) Abrir PDF en nueva pestaña si existe
    try:
        pdf_elem = driver.find_element(
            By.XPATH, "//a[contains(@href,'fichaTecnicaPDFDescargar')]"
        )
        pdf_href = pdf_elem.get_attribute("href")
        driver.execute_script("window.open(arguments[0], '_blank');", pdf_href)
        logging.info(f"PDF abierto en nueva pestaña: {pdf_href}")
    except:
        logging.warning("No se encontró ficha técnica (PDF)")

    # NO cerramos el navegador

if __name__ == "__main__":
    main()
