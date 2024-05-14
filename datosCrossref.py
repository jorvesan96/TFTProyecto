from habanero import Crossref
import datetime
import re
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

def extract_paragraphs(text):
    paragraphs = re.findall(r'<jats:p>(.*?)</jats:p>', text, re.DOTALL)
    merged_text = '\n'.join(paragraphs)
    return merged_text

spark = SparkSession.builder.appName("Crossref_DOIs").getOrCreate()

fecha_desde = datetime.datetime.now() - datetime.timedelta(days=1)

cr = Crossref()

resultados = cr.works(query=f"from-pub-date:{fecha_desde.strftime('%Y-%m-%d')}")

data=[]

for item in resultados['message']['items']:
    doi = item['DOI']
    autores = [f"{autor.get('given', '')} {autor.get('family', '')}" for autor in item.get('author', [])]
    autores = ', '.join(autores) if autores else ''
    resumen = extract_paragraphs(item.get('abstract', ''))
    fecha_registro = item.get('created', {}).get('date-time', '')
    data.append((doi, autores, resumen, fecha_registro))

schema = StructType([
    StructField("doi", StringType(), True),
    StructField("authors", StringType(), True),
    StructField("abstract", StringType(), True),
    StructField("created_date", StringType(), True)
])

df = spark.createDataFrame(data, schema=schema)

ruta_salida_hdfs = "hdfs:///datos"

df.write.format("parquet").mode("overwrite").save(ruta_salida_hdfs)

print("DataFrame almacenado en HDFS en:", ruta_salida_hdfs)

spark.stop()
