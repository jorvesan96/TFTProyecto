from habanero import Crossref
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
import re

# Configuración de HDFS y Spark
HDFS_URL = 'hdfs://alpha.eii-cluster.org:9000'
HDFS_USER = 'eii'
HDFS_PATH_PROCESSED = '/datos/input_data'

def extract_paragraphs(text):
    paragraphs = re.findall(r'<jats:p>(.*?)</jats:p>', text, re.DOTALL)
    merged_text = '\n'.join(paragraphs)
    return merged_text

# Función principal para descargar nuevos registros y procesarlos con Spark
def descargar_y_procesar_datos():
    cr = Crossref()
    fecha_actual = datetime.utcnow().strftime('%Y-%m-%d')
    nuevos_registros = []

    # Consulta a la API de CrossRef
    resultados = cr.works(filter={'from-update-date': fecha_actual}, limit=10)  # Obtener solo 10 registros

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
        df.show()

        # Guardar resultados procesados en HDFS
        df.write.mode('append').csv(f'hdfs://localhost:9000{HDFS_PATH_PROCESSED}')

        # Finalizar la sesión Spark
        spark.stop()

        print(f'Se han añadido {len(nuevos_registros)} nuevos registros y se han guardado en HDFS.')
    else:
        print('No hay nuevos registros desde la última actualización.')

# Ejecutar la función principal para descargar y procesar datos
descargar_y_procesar_datos()
