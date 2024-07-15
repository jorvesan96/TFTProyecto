import requests
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
import re

HDFS_URL = 'hdfs://abaco.cicei.com:9000'
HDFS_PATH_PROCESSED = '/datos/input_data'

def extract_paragraphs(text):
    cleaned_text = re.sub(r'<jats:.*?>', '', text, flags=re.DOTALL)
    cleaned_text = re.sub(r'</jats:.*?>', '', cleaned_text, flags=re.DOTALL)
    cleaned_text = cleaned_text.strip()
    return cleaned_text

def format_date(created_date):
    try:
        date_parts = created_date.get('date-parts', [[0, 0, 0]])
        dt = datetime(date_parts[0][0], date_parts[0][1], date_parts[0][2])
        return dt.strftime('%Y-%m-%d')
    except Exception as e:
        return ''

def consulta_crossref(fecha_desde, fecha_hasta, cursor=None):
    base_url = 'https://api.crossref.org/works'
    params = {
        'filter': f'from-update-date:{fecha_desde.isoformat()},until-update-date:{fecha_hasta.isoformat()}'
    }
    if cursor:
        params['cursor'] = cursor
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        return None


def descargar_y_procesar_datos():
    fecha_desde = datetime(2021, 7, 1).date()
    fecha_hasta = datetime.today().date()
    cursor = '*' 

    while cursor is not None:
        nuevos_registros = []
        
        resultados = consulta_crossref(fecha_desde, fecha_hasta, cursor=cursor)
        
        if not resultados:
            break
        
        if 'message' in resultados and 'next-cursor' in resultados['message']:
            cursor = resultados['message']['next-cursor']
        else:
            cursor = None
        
        if 'message' in resultados and 'items' in resultados['message']:
            nuevos_registros = resultados['message']['items']
        
        if nuevos_registros:
            datos_procesados = []

            for item in nuevos_registros:
                doi = item['DOI']
                titulo = item.get('title', [''])[0]
                autores = [f"{autor.get('given', '')} {autor.get('family', '')}" for autor in item.get('author', [])]
                autores = ', '.join(autores) if autores else ''
                resumen = extract_paragraphs(item.get('abstract', ''))
                
                fecha_creacion = format_date(item.get('created', ''))

                datos_procesados.append((doi, titulo, autores, resumen, fecha_creacion))

            spark = SparkSession.builder \
                .appName("CrossRef Data Processing") \
                .getOrCreate()  

            schema = StructType([
                StructField("doi", StringType(), True),
                StructField("title", StringType(), True),
                StructField("authors", StringType(), True),
                StructField("abstract", StringType(), True),
                StructField("creation_date", StringType(), True)
            ])

            df = spark.createDataFrame(datos_procesados, schema=schema)

            df.show()

            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_parquet_path = f'{HDFS_URL}{HDFS_PATH_PROCESSED}'

            df.write.mode('append').option("header", "true").parquet(output_parquet_path)

            spark.stop()

            print(f'Se han añadido {len(nuevos_registros)} nuevos registros y se han guardado en el archivo Parquet {output_parquet_path}.')
        else:
            print('No hay nuevos registros publicados dentro del rango de fechas especificado.')

descargar_y_procesar_datos()

