import os
import json
from pathlib import Path

# Subcadena que identifica la <dd> que contiene la descripción buscada
SEARCH_SUBSTRING = (
    "<dd>Teclado Bluetooth, con Touchpad de 4.5” integrado"
)

# Carpeta donde están los JSON de productos
input_folder = Path(
    r"C:\Users\Usuario\Documents\BitAndByte\Pruebas\caracteristicas-principales\productos-consumible-hp"
)

# Carpeta del script (aquí se guardará el JSON de salida)
script_folder = Path(__file__).parent

skus_encontrados = []

for json_file in input_folder.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        producto = json.load(f)

    # Asegurarnos de tener siempre un string (no None)
    html = producto.get("custom_caracteristicas") or ""

    # Si encontramos la subcadena en el HTML, extraemos el SKU
    if SEARCH_SUBSTRING in html:
        for variante in producto.get("variants", []):
            sku = variante.get("sku")
            if sku:
                skus_encontrados.append(sku)
                break

# Eliminar duplicados
skus_unicos = list(dict.fromkeys(skus_encontrados))

# Preparar lista de objetos {"sku": ...}
output_list = [{"sku": sku} for sku in skus_unicos]

# Guardar el resultado
output_file = script_folder / "skus_encontrados.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_list, f, indent=2, ensure_ascii=False)

# Mostrar conteo y lista
print(f"Total de SKUs encontrados: {len(skus_unicos)}")
print(json.dumps(output_list, indent=2, ensure_ascii=False))
