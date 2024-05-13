from habanero import Crossref
import datetime
import re
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

def extract_paragraphs(text):
    # Encuentra todos los bloques <jats:p>...</jats:p> y extrae el texto contenido en ellos
    paragraphs = re.findall(r'<jats:p>(.*?)</jats:p>', text, re.DOTALL)
    # Une los párrafos en un solo bloque de texto
    merged_text = '\n'.join(paragraphs)
    return merged_text

spark = SparkSession.builder.appName("Crossref_DOIs").getOrCreate()

# Fecha desde la que deseas obtener los DOIs (por ejemplo, ayer)
fecha_desde = datetime.datetime.now() - datetime.timedelta(days=1)

# Instancia la clase Crossref
cr = Crossref()

# Busca los DOIs desde la fecha especificada hasta hoy
resultados = cr.works(query=f"from-pub-date:{fecha_desde.strftime('%Y-%m-%d')}")

schema = ['doi']
data=[]
# Imprime los DOIs encontrados
for item in resultados['message']['items']:
    doi = item['DOI']
    #autores = ", ".join([f"{autor.get('given', 'No disponible')} {autor.get('family', 'No disponible')}" for autor in item.get('author', [])])
    #resumen = extract_paragraphs(item.get('abstract', 'No disponible'))
    #fecha_registro = item['created']['date-time']
    data.append((doi))
print(data)
longitud_schema = len(schema)
longitud_data = len(data[0])

print(f"Longitud de schema: {longitud_schema}")
print(f"Longitud de data: {longitud_data}")

df = spark.createDataFrame(data, schema=schema)
df.show()
spark.stop()
