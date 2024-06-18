from habanero import Crossref
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
import re

# Configuración de HDFS y Spark
HDFS_URL = 'hdfs://abaco.cicei.com:9000'
HDFS_USER = 'jorvesan'
HDFS_PATH_PROCESSED = '/datos/input_data'

def extract_paragraphs(text):
    paragraphs = re.findall(r'<jats:p>(.*?)</jats:p>', text, re.DOTALL)
    merged_text = '\n'.join(paragraphs)
    return merged_text

def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except Exception as e:
        return ''

# Función principal para descargar nuevos registros y procesarlos con Spark
def descargar_y_procesar_datos():
    cr = Crossref()
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    pagina = 0
    total_resultados = 1  # Inicializado con un valor que permita entrar en el bucle
    
    while pagina * 20 < total_resultados:
        nuevos_registros = []
        
        # Consulta a la API de CrossRef
        resultados = cr.works(filter={'from-update-date': fecha_actual}, offset=pagina * 20)
        
        if 'message' in resultados and 'total-results' in resultados['message']:
            total_resultados = resultados['message']['total-results']
        
        if 'message' in resultados and 'items' in resultados['message']:
            nuevos_registros = resultados['message']['items']
        
        if nuevos_registros:
            # Inicializar lista para almacenar datos procesados
            datos_procesados = []

            # Extraer campos relevantes de cada registro
            for item in nuevos_registros:
                doi = item['DOI']
                titulo = item.get('title', [''])[0]
                autores = [f"{autor.get('given', '')} {autor.get('family', '')}" for autor in item.get('author', [])]
                autores = ', '.join(autores) if autores else ''
                resumen = extract_paragraphs(item.get('abstract', ''))
                fecha_registro = format_date(item.get('created', {}).get('date-time', ''))
                datos_procesados.append((doi, titulo, autores, resumen, fecha_registro))

            # Inicializar SparkSession
            spark = SparkSession.builder \
                .appName("CrossRef Data Processing") \
                .getOrCreate()  

            schema = StructType([
                StructField("doi", StringType(), True),
                StructField("title", StringType(), True),
                StructField("authors", StringType(), True),
                StructField("abstract", StringType(), True),
                StructField("created_date", StringType(), True)
            ])

            # Crear DataFrame de Spark
            df = spark.createDataFrame(datos_procesados, schema=schema)

            # Mostrar algunos registros
            df.show()

            # Generar nombre de archivo CSV con marca de tiempo
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_csv_path = f'{HDFS_URL}{HDFS_PATH_PROCESSED}'
            df = df.repartition(1)
            # Guardar resultados procesados en formato CSV
            df.write.mode('append').csv(output_csv_path)

            # Finalizar la sesión Spark
            spark.stop()

            print(f'Se han añadido {len(nuevos_registros)} nuevos registros y se han guardado en el archivo CSV {output_csv_path}.')
        else:
            print('No hay nuevos registros desde la última actualización.')

        pagina += 1

# Ejecutar la función principal para descargar y procesar datos
descargar_y_procesar_datos()