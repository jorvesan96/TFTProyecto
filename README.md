
# CROSSREFDATAPROCESSING

## Descripción de los Scripts

### 1. `descargaDatosInicial/procesadoDatos2021.py`

#### Descripción
Se procesan archivos JSON ubicados en `datosSinProcesar2021`, se limpian los datos y se estructuran en un formato tabular utilizando la biblioteca `pandas`. Los datos procesados se guardan en archivos Parquet en `datosProcesados2021`.

#### Requisitos
- Python
- pandas

#### Uso
Asegúrese de tener los directorios `datosSinProcesar2021` y `datosProcesados2021` configurados correctamente. Ejecute el script `procesar_datos.py` para procesar los archivos JSON y almacenar los resultados en formato Parquet. Estos datos deben cargarse en el HFDS con la instrucción: `hdfs dfs -put /datosProcesados2021/* /datos/input_data`

---

### 2. `descargaDatosInicial/descargaProcesadoDatos2024.py`

#### Descripción
Se utiliza la API de CrossRef a través de la biblioteca `habanero` para descargar artículos publicados recientemente. Los datos se procesan y se guardan en formato CSV en un sistema de archivos distribuido (HDFS).

#### Requisitos
- Python
- habanero
- pyspark

#### Configuración
Es necesario tener acceso a un sistema HDFS. Configure las variables `HDFS_URL`, `HDFS_USER`, y `HDFS_PATH_PROCESSED` en el script según el entorno de ejecución.

#### Uso
Ejecute el script `procesar_datos_crossref.py` para descargar y procesar los datos de CrossRef, y almacenar los resultados en formato CSV en HDFS.

---

### 3. `descargaDatosDiario/datosCrossref.py`

#### Descripción
Se utiliza la biblioteca `habanero` para consultar la API de CrossRef y obtener artículos publicados recientemente. Los datos se procesan y se guardan en formato Parquet en un directorio específico.

#### Requisitos
- Python
- habanero
- pyspark

#### Configuración
Es esencial tener acceso a un sistema HDFS. Configure las variables `HDFS_URL` y `HDFS_PATH_PROCESSED` en el script según el entorno de ejecución.

#### Uso
Ejecute el script `procesar_datos_habanero.py` para realizar consultas a la API de CrossRef, procesar los datos obtenidos y almacenar los resultados en formato Parquet en el sistema de archivos HDFS.

---

### 4. `servidorWeb`

### Configuración

Este proyecto incluye un servidor web implementado en Django que utiliza los siguientes archivos:

- `views.py`: Define las vistas del servidor web que interactúan con un servidor socket externo para obtener y procesar datos en tiempo real.

- `settings.py`: Contiene la configuración principal de la aplicación Django, incluyendo ajustes como la configuración de la base de datos, configuración del servidor, aplicaciones instaladas, configuración de archivos estáticos y más.

- `urls`: Define las rutas de URL para la aplicación Django, especificando cómo las solicitudes HTTP se asignan a las vistas en `views.py`.

El servidor web proporciona las siguientes funcionalidades:

- **Página de Inicio (`index.html`)**: Renderiza una página de inicio básica.
- **Procesamiento de Solicitudes (`process_request`)**: Endpoint para procesar solicitudes POST con palabras clave y fechas.
- **Resultados (`show_results`)**: Muestra resultados de análisis de sentimiento en un gráfico basado en datos obtenidos del servidor socket.
- **Nube de Palabras (`show_word_cloud_results`)**: Muestra una nube de palabras basada en datos obtenidos del servidor socket.
- **Punto Final de Polling (`polling_endpoint_results` y `polling_endpoint_word_cloud`)**: Puntos finales para realizar consultas automáticas al servidor socket y obtener resultados.


### Uso

1. Asegúrese de tener todas las dependencias instaladas y configuradas correctamente.
2. Ejecute el servidor web Django usando el comando `python manage.py runserver`.
3. Acceda a las diferentes funcionalidades a través de las rutas definidas en `urls.py` y las vistas implementadas en `views.py`.

### 5. `CrossrefTFT`

#### Descripción
Este proyecto implica el procesamiento de datos de CrossRef utilizando Spark. Se utiliza un script llamado run_processing.sh para automatizar el proceso de limpiar, compilar y ensamblar el código Scala en un archivo JAR ejecutable (CrossrefDataProcessing.jar). Este archivo JAR se utilizará luego con spark-submit para ejecutar el procesamiento de datos en un entorno distribuido.

#### Configuración
1. **Requisitos Previos:**
 - **Scala Build Tool (SBT):** Asegúrese de tener SBT instalado y configurado correctamente en tu sistema.

2. **Contenido de `run_processing.sh`:**
   El script `run_processing.sh` realiza los siguientes pasos:

   ```bash
   #!/bin/bash
   
   # Limpiar compilaciones anteriores
   sbt clean
   
   # Compilar el código Scala
   sbt compile
   
   # Ensamblar el código y las dependencias en un archivo JAR
   sbt assembly

clean: Este comando limpia cualquier compilación previa del proyecto.
compile: Compile el código Scala para asegurarse de que esté actualizado.
assembly: Ensamble el código y todas las dependencias en un archivo JAR ejecutable (CrossrefDataProcessing.jar).


3. **Ejecución de `spark-submit`:**
Después de ejecutar run_processing.sh y asegurese de que el archivo JAR (CrossrefDataProcessing.jar) se ha generado correctamente en el directorio target/scala-2.12/, se puede utilizar spark-submit para ejecutar el proceso debe ubicarse en CrossrefTFT/ . Aquí está el comando:
```bash
spark-submit \
  --class CrossrefDataProcessing \
  --master yarn \
  --deploy-mode cluster \
  --conf spark.sql.parquet.filterPushdown=true \
  --conf spark.sql.parquet.cacheMetadata=true \
  --conf spark.driver.memory=8g \
  --conf spark.driver.memoryOverhead=1g \
  --conf spark.dynamicAllocation.enabled=true \
  --conf spark.shuffle.service.enabled=true \
  --conf spark.files.io.connectionTimeout=1000s \
  --conf spark.memory.fraction=0.8 \
  --conf spark.memory.storageFraction=0.2 \
  --conf spark.executor.extraJavaOptions="-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=35" \
  target/scala-2.12/CrossrefDataProcessing.jar
  