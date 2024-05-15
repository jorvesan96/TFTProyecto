from habanero import Crossref
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
import re

# Configuración de HDFS y Spark
HDFS_URL = 'hdfs://alpha.eii-cluster.org:9000'
HDFS_USER = 'eii'
HDFS_PATH_PROCESSED = '/datos/processed_crossref_data'
LAST_UPDATE_PATH = '/datos/last_update.txt'



def extract_paragraphs(text):
    paragraphs = re.findall(r'<jats:p>(.*?)</jats:p>', text, re.DOTALL)
    merged_text = '\n'.join(paragraphs)
    return merged_text

# Función para obtener la fecha de la última actualización en formato timestamp
def obtener_fecha_ultima_actualizacion():
    try:
        with open(LAST_UPDATE_PATH, 'r') as file:
            fecha_str = file.read().strip()
            return int(datetime.strptime(fecha_str, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp())
    except FileNotFoundError:
        return 946684800   # Fecha inicial por defecto (1 de enero de 2000 en timestamp)

# Función para guardar la fecha de la última actualización en un archivo
def guardar_fecha_ultima_actualizacion(fecha):
    with open(LAST_UPDATE_PATH, 'w') as file:
        file.write(fecha)

# Función principal para descargar nuevos registros y procesarlos con Spark
def descargar_y_procesar_datos():
    cr = Crossref()
    ultima_fecha = obtener_fecha_ultima_actualizacion()
    nuevos_registros = []

    # Consulta a la API de CrossRef
    resultados = cr.works(filter={'from-update-date': ultima_fecha}, limit=10)  # Obtener solo 10 registros

    if 'message' in resultados and 'items' in resultados['message']:
        nuevos_registros = resultados['message']['items']

    if nuevos_registros:
        # Inicializar lista para almacenar datos procesados
        datos_procesados = []

        # Extraer campos relevantes de cada registro
        for item in nuevos_registros:
            doi = item['DOI']
            autores = [f"{autor.get('given', '')} {autor.get('family', '')}" for autor in item.get('author', [])]
            autores = ', '.join(autores) if autores else ''
            resumen = extract_paragraphs(item.get('abstract', ''))
            fecha_registro = item.get('created', {}).get('date-time', '')
            datos_procesados.append((doi, autores, resumen, fecha_registro))

        # Inicializar SparkSession
        spark = SparkSession.builder \
            .appName("CrossRef Data Processing") \
            .master("yarn") \
            .getOrCreate()  

        schema = StructType([
            StructField("doi", StringType(), True),
            StructField("authors", StringType(), True),
            StructField("abstract", StringType(), True),
            StructField("created_date", StringType(), True)
        ])

        # Crear DataFrame de Spark
        df = spark.createDataFrame(datos_procesados, schema=schema)

        # Mostrar algunos registros
        df.show(truncate=False)

        # Guardar resultados procesados en HDFS
        df.write.mode('overwrite').parquet(f'hdfs://localhost:9000{HDFS_PATH_PROCESSED}')

        # Finalizar la sesión Spark
        spark.stop()

        # Actualizar la fecha de la última actualización
        guardar_fecha_ultima_actualizacion(datetime.now().strftime('%Y-%m-%d'))

        print(f'Se han añadido {len(nuevos_registros)} nuevos registros y se han guardado en HDFS.')
    else:
        print('No hay nuevos registros desde la última actualización.')

# Ejecutar la función principal para descargar y procesar datos
descargar_y_procesar_datos()
