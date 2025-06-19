import json

# 1) Carga de archivos
with open('skus_encontrados.json', 'r', encoding='utf-8') as f:
    skus_data = json.load(f)

with open('productos_especiales_TXL0233.json', 'r', encoding='utf-8') as f:
    productos_data = json.load(f)

# 2) Extrae la lista de SKUs a buscar
skus_encontrados = {item['sku'] for item in skus_data}

# 3) Separa en dos listas: coincidencias y no coincidencias
coincidencias = []
no_coincidencias = []

for producto in productos_data:
    clave = producto.get('clave')
    if clave in skus_encontrados:
        coincidencias.append(producto)
    else:
        no_coincidencias.append(producto)

# 4) Guarda los dos archivos JSON
with open('coincidencias.json', 'w', encoding='utf-8') as f:
    json.dump(coincidencias, f, ensure_ascii=False, indent=4)

with open('no_coincidencias.json', 'w', encoding='utf-8') as f:
    json.dump(no_coincidencias, f, ensure_ascii=False, indent=4)

print(f"Guardadas {len(coincidencias)} coincidencias en 'coincidencias.json'")
print(f"Guardados {len(no_coincidencias)} no-coincidencias en 'no_coincidencias.json'")
