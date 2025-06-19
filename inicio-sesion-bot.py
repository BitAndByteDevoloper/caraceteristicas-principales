import os
import time
import random
import logging
import chromedriver_autoinstaller
import pyautogui

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# ---------------------------------------
# Carga de entorno y librerías
# ---------------------------------------
load_dotenv()

# ---------------------------------------
# Configuración de logging
# ---------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)

# ---------------------------------------
# Coordenadas fijas de interfaz
# ---------------------------------------
REFRESH_X, REFRESH_Y = 98, 61      # “Recargar” del navegador
CHECKBOX_X, CHECKBOX_Y = 531, 373  # casilla de Cloudflare

# ---------------------------------------
# Movimiento suave del ratón (comportamiento humano)
# ---------------------------------------
def human_like_slide_to(x_target, y_target):
    x_start, y_start = pyautogui.position()
    steps = random.randint(10, 15)
    for i in range(steps):
        xi = int(x_start + (x_target - x_start) * (i + 1) / steps)
        yi = int(y_start + (y_target - y_start) * (i + 1) / steps)
        pyautogui.moveTo(xi, yi, duration=random.uniform(0.01, 0.03))
    pyautogui.moveTo(x_target, y_target, duration=random.uniform(0.02, 0.05))

# ---------------------------------------
# Clic en “Recargar”
# ---------------------------------------
def click_refresh():
    logging.info(f"Clic en Recargar @ ({REFRESH_X},{REFRESH_Y})")
    human_like_slide_to(REFRESH_X, REFRESH_Y)
    pyautogui.click()

# ---------------------------------------
# Clic en la casilla de Cloudflare
# ---------------------------------------
def click_checkbox():
    if random.random() < 0.2:
        human_like_slide_to(CHECKBOX_X + 10, CHECKBOX_Y + 10)
        pyautogui.click()
        time.sleep(random.uniform(0.1, 0.3))
    logging.info(f"Clic en checkbox @ ({CHECKBOX_X},{CHECKBOX_Y})")
    human_like_slide_to(CHECKBOX_X, CHECKBOX_Y)
    pyautogui.click()

# ---------------------------------------
# Comprueba si la casilla sigue visible
# ---------------------------------------
def is_checkbox_present(template='checkbox.png', confidence=0.8):
    try:
        return pyautogui.locateOnScreen(template, confidence=confidence) is not None
    except:
        return False

# ---------------------------------------
# Bypass del challenge de Cloudflare
# ---------------------------------------
def bypass_cloudflare():
    click_refresh()
    logging.info("Esperando 3.0s antes de verificar aparición del checkbox")
    time.sleep(3)

    click_checkbox()
    initial_pause = random.uniform(10, 15)
    logging.info(f"Pausa inicial tras clic en checkbox: {initial_pause:.1f}s")
    time.sleep(initial_pause)

    attempts = 0
    while is_checkbox_present():
        attempts += 1
        pause = random.uniform(10, 15)
        logging.info(f"[Cloudflare] Intento {attempts}: checkbox visible → espera {pause:.1f}s")
        time.sleep(pause)
        click_checkbox()

    logging.info("[Cloudflare] Challenge superado")

# ---------------------------------------
# Inicializa Selenium con flags anti-detección
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
    opts.add_experimental_option("detach", True)

    logging.info("Inicializando ChromeDriver")
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=opts)
    driver.set_page_load_timeout(60)
    return driver

# ---------------------------------------
# Flujo principal
# ---------------------------------------
def main():
    CT_EMAIL = os.getenv("CT_EMAIL_CENTINELA")
    CT_PASSWORD = os.getenv("CT_PASSWORD_CENTINELA")
    if not CT_EMAIL or not CT_PASSWORD:
        logging.error("Faltan CT_EMAIL_CENTINELA o CT_PASSWORD_CENTINELA en el entorno")
        return

    driver = setup_selenium()
    login_url = "https://ctonline.mx/iniciar/correo"
    logging.info(f"Abrir login: {login_url}")
    driver.get(login_url)
    time.sleep(5)

    logging.info("Invocando bypass de Cloudflare")
    bypass_cloudflare()

    logging.info("Procediendo al login")
    wait = WebDriverWait(driver, 20)
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "correo")))
    email_input.send_keys(CT_EMAIL)
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(CT_PASSWORD + Keys.RETURN)

    # ---> Esperamos ahora a que la URL sea exactamente la home "/"
    wait.until(EC.url_to_be("https://ctonline.mx/"))
    logging.info("Login completado: estamos en la home https://ctonline.mx/")

if __name__ == "__main__":
    main()
