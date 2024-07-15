import json
import os
import re
import pandas as pd

def extract_paragraphs(text):
    cleaned_text = re.sub(r'<jats:.*?>', '', text, flags=re.DOTALL)
    cleaned_text = re.sub(r'</jats:.*?>', '', cleaned_text, flags=re.DOTALL)
    cleaned_text = cleaned_text.strip()
    return cleaned_text

def obtener_fecha_yyyymmdd(fecha_completa):
    if not fecha_completa:
        return ''
    match = re.search(r'\d{4}-\d{2}-\d{2}', fecha_completa)
    if match:
        return match.group()
    else:
        return ''

directorio_entrada = '~/datosSinProcesar2021'
directorio_salida = '~/datosProcesados2021'

for filename in os.listdir(directorio_entrada):
    if filename.endswith('.json'):
        nombre_sin_extension = os.path.splitext(filename)[0]
        filepath = os.path.join(directorio_entrada, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            datos_procesados = []
            for item in data['items']:
                doi = item.get('DOI', '')
                title_list = item.get('title', [])
                title = title_list[0] if title_list else '' 
                
                authors = ', '.join([f"{author.get('given', '')} {author.get('family', '')}" for author in item.get('author', [])])
                
                abstract_clean = extract_paragraphs(item.get('abstract', ''))
                
                fecha_creacion_completa = item['created']['date-time'] if 'created' in item else ''
                
                fecha_creacion = obtener_fecha_yyyymmdd(fecha_creacion_completa)
                
                datos_procesados.append({
                    'doi': doi,
                    'title': title,
                    'authors': authors,
                    'abstract': abstract_clean,
                    'creation_date': fecha_creacion
                })
            
            df = pd.DataFrame(datos_procesados)
            
            output_filepath = os.path.join(directorio_salida, f'{nombre_sin_extension}.parquet')
            df.to_parquet(output_filepath, index=False)
            
            print(f'Datos procesados de {filename} guardados en {output_filepath}')

