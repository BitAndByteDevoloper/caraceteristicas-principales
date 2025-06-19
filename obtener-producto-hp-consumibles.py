import os
import json
import locale
import time
import random
from pathlib import Path

import requests
from dotenv import load_dotenv

# 1) Carga de entorno y configuración regional
load_dotenv()
locale.setlocale(locale.LC_NUMERIC, '')

# 2) Parámetros de la tienda Shopify
shop_name    = os.getenv('SHOPIFY_SHOP_NAME')
access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
api_version  = '2024-07'
base_url     = f"https://{shop_name}.myshopify.com/admin/api/{api_version}/products.json"

headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": access_token
}

# 3) Carpeta de salida para los JSON
output_folder = Path(
    r"C:\Users\Usuario\Documents\BitAndByte\Pruebas\caracteristicas-principales\productos-consumible-hp"
)
output_folder.mkdir(parents=True, exist_ok=True)

def fetch_metafield(product_id, namespace, key):
    """
    Obtiene con backoff y pausa el valor del metafield indicado para el producto.
    """
    url = (
        f"https://{shop_name}.myshopify.com/"
        f"admin/api/{api_version}/products/{product_id}/metafields.json"
    )
    params = {"namespace": namespace, "key": key}
    backoff = 1.0

    while True:
        time.sleep(0.6 + random.random() * 0.2)
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 429:
            ra_header = resp.headers.get("Retry-After")
            retry_after = float(ra_header) if ra_header is not None else backoff
            print(f"    Rate limit alcanzado. Reintentando en {retry_after}s...")
            time.sleep(retry_after)
            backoff = min(backoff * 2, 60.0)
            continue
        resp.raise_for_status()
        mets = resp.json().get("metafields", [])
        return mets[0].get("value") if mets else None

def fetch_and_save_all_hp_consumibles():
    page = 1
    total_saved = 0
    next_url = base_url
    params = {"limit": 250, "vendor": "HP", "product_type": "Consumibles"}

    while next_url:
        print(f"Obteniendo página {page}...")
        resp = requests.get(
            next_url,
            headers=headers,
            params=params if next_url == base_url else None
        )
        resp.raise_for_status()
        batch = resp.json().get("products", [])
        print(f"Página {page}: {len(batch)} productos recuperados")

        for product in batch:
            product_id = product["id"]
            product["custom_caracteristicas"] = fetch_metafield(
                product_id, "custom", "caracteristicas"
            )
            for variant in product.get("variants", []):
                sku = variant.get("sku")
                if not sku:
                    continue
                output_file = output_folder / f"{sku}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(product, f, indent=2, ensure_ascii=False)
                total_saved += 1
                print(f"  [{total_saved}] Guardado SKU: {sku}")

        link_header = resp.headers.get("Link", "")
        next_url = None
        if link_header:
            links = requests.utils.parse_header_links(
                link_header.rstrip('>').replace('>,', '>,')
            )
            for link in links:
                if link.get("rel") == "next":
                    next_url = link.get("url")
                    break

        page += 1

    print(f"Hecho. Total de archivos guardados: {total_saved}")

if __name__ == "__main__":
    fetch_and_save_all_hp_consumibles()
