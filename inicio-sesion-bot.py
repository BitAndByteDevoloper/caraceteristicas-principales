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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    logging.info(f"Moviendo ratón a ({x},{y}) de forma humana")
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
    logging.info("Clic en botón Recargar/Detener")
    human_like_slide_to(REFRESH_X, REFRESH_Y)
    pyautogui.click()

def click_checkbox():
    logging.info("Clic en checkbox 'No soy un robot'")
    if random.random() < 0.2:
        human_like_slide_to(CHECKBOX_X + 10, CHECKBOX_Y + 10)
        pyautogui.click()
        time.sleep(random.uniform(0.1, 0.3))
    human_like_slide_to(CHECKBOX_X, CHECKBOX_Y)
    pyautogui.click()

def is_checkbox_present():
    try:
        present = pyautogui.locateOnScreen(CHECKBOX_IMG, confidence=0.8) is not None
        logging.info(f"Checkbox presente: {present}")
        return present
    except Exception as e:
        logging.warning(f"Error al detectar checkbox: {e}")
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
    logging.info("Esperando 10s para aparición del checkbox")
    time.sleep(10)
    click_checkbox()
    pause = random.uniform(10, 15)
    logging.info(f"Espera tras click checkbox: {pause:.1f}s")
    time.sleep(pause)
    while is_checkbox_present():
        pause = random.uniform(10, 15)
        logging.info(f"Reintento checkbox: esperando {pause:.1f}s")
        time.sleep(pause)
        click_checkbox()
    logging.info("Bypass Cloudflare completado")

# ---------------------------------------
# Configuración de Selenium
# ---------------------------------------
def setup_selenium():
    logging.info("Instalando/configurando ChromeDriver")
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
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=opts)
    driver.set_page_load_timeout(90)
    logging.info("ChromeDriver iniciado")
    return driver

# ---------------------------------------
# Flujo principal
# ---------------------------------------
def main():
    logging.info("Inicio del proceso completo")
    # 1) Leer credenciales
    email = os.getenv("CT_EMAIL_CENTINELA")
    pwd   = os.getenv("CT_PASSWORD_CENTINELA")
    if not email or not pwd:
        logging.error("Credenciales faltantes en .env")
        return

    driver = setup_selenium()

    # 2) Login (con bypass)
    logging.info("Navegando a página de login")
    driver.get("https://ctonline.mx/iniciar/correo")
    time.sleep(5)
    bypass_cloudflare()
    logging.info("Recargando formulario de login tras bypass")
    driver.get("https://ctonline.mx/iniciar/correo")
    time.sleep(3)

    try:
        logging.info("Esperando formulario de login")
        wait = WebDriverWait(driver, 20)
        inp = wait.until(EC.presence_of_element_located((By.NAME, "correo")))
        inp.send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(pwd + Keys.RETURN)
        wait.until(EC.url_contains("ctonline.mx"))
        logging.info("Login exitoso")
    except TimeoutException:
        logging.error("Error: formulario de login no detectado")
        return

    # 3) Leer JSON y primer SKU
    json_path = os.path.join(SCRIPT_DIR, "coincidencias.json")
    logging.info(f"Cargando SKUs desde {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    sku = products[0].get("clave")
    logging.info(f"Primer SKU seleccionado: {sku}")

    # Crear carpetas
    descarga_dir = os.path.join(SCRIPT_DIR, "descarga-archivos", sku)
    for sub in ['Caracteristicas','FichaTecnica','PDF','Folleto','JSON']:
        path = os.path.join(descarga_dir, sub)
        os.makedirs(path, exist_ok=True)
        logging.info(f"Carpeta creada: {path}")

    # 4) Búsqueda del producto
    search_url = f"https://ctonline.mx/buscar/productos?b={sku}"
    logging.info(f"Navegando a búsqueda: {search_url}")
    driver.get(search_url)
    time.sleep(10)
    ct = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "ct-description"))
    )
    try:
        link = ct.find_element(By.CSS_SELECTOR, "h6 a").get_attribute("href")
    except NoSuchElementException:
        link = ct.find_element(By.CSS_SELECTOR, "h5 a").get_attribute("href")
    logging.info(f"Enlace de detalle encontrado: {link}")

    # 5) Detalle en nueva pestaña
    logging.info("Abriendo detalle en nueva pestaña")
    driver.execute_script("window.open(arguments[0], '_blank');", link)
    driver.switch_to.window(driver.window_handles[-1])

    # 6) Esperar despliegue ficha técnica
    logging.info("Esperando desplegar ficha técnica")
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#ct_technical.in"))
    )
    time.sleep(10)

    # 7) Guardar características principales (opcional si existe)
    try:
        logging.info("Extraer características principales")
        features_el = driver.find_element(By.CSS_SELECTOR, "#ct_features .panel-body p")
        feat_file = os.path.join(descarga_dir, 'Caracteristicas', f"{sku}_caracteristicas.html")
        with open(feat_file, "w", encoding="utf-8") as f:
            f.write(f"<div class='panel-body'>{features_el.get_attribute('outerHTML')}</div>")
        logging.info(f"Características guardadas en {feat_file}")
    except NoSuchElementException:
        logging.warning("No se encontró sección de características principales")

    # 8) Guardar ficha técnica (información adicional)
    try:
        logging.info("Extraer ficha técnica")
        info_sections = driver.find_elements(
            By.CSS_SELECTOR, "div.panel-body#ficha_tecnica > div.ct-section"
        )
        if info_sections:
            info_html = "\n".join(sec.get_attribute("outerHTML") for sec in info_sections)
            info_file = os.path.join(descarga_dir, 'FichaTecnica', f"{sku}_ficha_tecnica.html")
            with open(info_file, "w", encoding="utf-8") as f:
                f.write(f"<div id='ficha_tecnica'>{info_html}</div>")
            logging.info(f"Ficha técnica guardada en {info_file}")
        else:
            logging.warning("No se encontró información adicional (ficha técnica)")
    except Exception as e:
        logging.error(f"Error extrayendo ficha técnica: {e}")

    # 9) Descargar PDF técnico
    try:
        logging.info("Buscando enlace PDF técnico")
        pdf_elem = driver.find_element(By.XPATH, "//a[contains(@href,'fichaTecnicaPDFDescargar')]")
        href = pdf_elem.get_attribute("href")
        logging.info(f"Descargando PDF técnico desde {href}")
        resp = requests.get(href, timeout=30)
        pdf_path = os.path.join(descarga_dir, 'PDF', f"{sku}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(resp.content)
        logging.info(f"PDF técnico guardado en {pdf_path}")
    except NoSuchElementException:
        logging.warning("No se encontró ficha técnica (PDF)")

    # 10) Descargar folleto Icecat y renombrar con SKU
    try:
        logging.info("Buscando enlace de folleto Icecat")
        icecat = driver.find_element(By.CSS_SELECTOR, "div.-icecat-ds_data.-text a")
        icecat_href = icecat.get_attribute("href")
        logging.info(f"Descargando folleto Icecat desde {icecat_href}")
        resp2 = requests.get(icecat_href, timeout=30)
        fol_path = os.path.join(descarga_dir, 'Folleto', f"{sku}_folleto.pdf")
        with open(fol_path, "wb") as f:
            f.write(resp2.content)
        logging.info(f"Folleto Icecat guardado en {fol_path}")
    except NoSuchElementException:
        logging.warning("No se encontró folleto Icecat")

    # 11) Guardar JSON original
    json_out = os.path.join(descarga_dir, 'JSON', f"{sku}.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(products[0], f, ensure_ascii=False, indent=4)
    logging.info(f"JSON guardado en {json_out}")

    logging.info("Proceso completo, navegador queda abierto para inspección")

if __name__ == "__main__":
    main()
