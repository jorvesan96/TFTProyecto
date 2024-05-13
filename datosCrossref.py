import requests
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

def fetch_latest_dois(num_dois):
    url = f'https://api.crossref.org/works?sort=created&order=desc&rows={num_dois}'
    response = requests.get(url)
    if response.status_code == 200:
        dois_data = response.json()
        items = dois_data['message']['items']
        doi_metadata = []
        for item in items:
            metadata = {
                "titulo": item['title'][0] if 'title' in item else None,
                "doi": item['DOI'] if 'DOI' in item else None,
                "autor": ", ".join([f"{author['given']} {author['family']}" for author in item['author']]) if 'author' in item else None,
                "abstract": item['abstract'] if 'abstract' in item else None
            }
            doi_metadata.append(metadata)
        return doi_metadata
    else:
        print("Error al obtener los últimos DOIs:", response.status_code)
        return None

if __name__ == "__main__":
    num_dois = 3  # Cambia esto al número deseado de DOIs a obtener
    latest_dois_metadata = fetch_latest_dois(num_dois)
    if latest_dois_metadata:
        # Inicializar sesión de Spark
        spark = SparkSession.builder.appName("Fetch and Save DOIs").getOrCreate()
        # Especificar el esquema del DataFrame
        schema = StructType([
            StructField("titulo", StringType(), nullable=True),
            StructField("doi", StringType(), nullable=True),
            StructField("autor", StringType(), nullable=True),
            StructField("abstract", StringType(), nullable=True),
            # Aquí puedes agregar más campos según la estructura de tus datos
        ])
        # Crear DataFrame a partir de los datos
        doi_df = spark.createDataFrame(latest_dois_metadata, schema=schema)
        # Escribir el DataFrame en HDFS en modo append
        doi_df.write.mode("overwritte").parquet("/datos")
        print(f"{num_dois} últimos DOIs guardados en HDFS")
