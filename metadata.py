import os
import json
import csv

def procesar_archivos_json(directorio_json, directorio_destino):
    if not os.path.exists(directorio_destino):
        os.makedirs(directorio_destino)

    for archivo_json in os.listdir(directorio_json):
        if archivo_json.endswith('.json'):
            contador = 0  # Reiniciar el contador para cada archivo JSON
            ruta_json = os.path.join(directorio_json, archivo_json)
            nombre_csv = os.path.splitext(archivo_json)[0] + '.csv'  # Nombre del archivo CSV basado en el JSON
            ruta_csv = os.path.join(directorio_destino, nombre_csv)

            with open(ruta_json, 'r', encoding='utf-8') as file:
                data = json.load(file)
                items = data.get('items', [])
                with open(ruta_csv, 'w', newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    for item in items:
                        indexed_data = item.get('indexed', {})
                        doi = item.get('DOI', '')
                        title_list = item.get('title', [''])
                        title = title_list[0] if title_list else ''
                        authors = ', '.join([f"{author.get('given', '')} {author.get('family', '')}" for author in item.get('author', [])])
                        abstract = item.get('abstract', '')
                        date_parts = indexed_data.get('date-parts', [[]])[0]
                        fecha_publicacion = '-'.join(map(str, date_parts)) if date_parts else ''

                        csv_writer.writerow([doi, title, authors, abstract, fecha_publicacion])
                        contador += 1

directorio_json = "/home/jorvesan/datosSinProcesar" 
directorio_destino = "/home/jorvesan/datosProcesados" 
procesar_archivos_json(directorio_json, directorio_destino)
print("Proceso completado.")

