import psycopg2
import pandas as pd
from sklearn.impute import SimpleImputer

# Conectar a la base de datos de PostgreSQL
conn = psycopg2.connect(
    dbname="grafana_ml_model", 
    user="postgres", 
    password="postgres", 
    host="localhost", 
    port="5432"
)

# Crear un cursor
cur = conn.cursor()

# Cargar los datos desde el archivo CSV
file_path = "/home/rolando/Kathy-Escuela/ML/csv/caso-EncuestasHoteles.csv"
data = pd.read_csv(file_path)

# Filtrar solo columnas numéricas
data = data.select_dtypes(include=['number'])

# Eliminar columnas que contienen solo valores NaN
data = data.dropna(axis=1, how='all')

# Manejar valores NaN imputando con la media de cada columna
imputer = SimpleImputer(strategy='mean')
data_imputed = pd.DataFrame(imputer.fit_transform(data), columns=data.columns)

# Descripción y creador para grafana_ml_model_index
db_name = "Encuesta Hoteles"
description = "Datos de encuesta sobre hoteles con múltiples características numéricas y categóricas."
creator = "archivo CSV"

# Insertar los datos en la tabla grafana_ml_model_index
cur.execute("""
    INSERT INTO grafana_ml_model_index (name, description, creator) 
    VALUES (%s, %s, %s) RETURNING id
""", (db_name, description, creator))

# Obtener el ID de la fila insertada
index_id = cur.fetchone()[0]

# Insertar los nombres de las características en la tabla grafana_ml_model_feature
feature_names = data_imputed.columns.tolist()  # Obtener los nombres de las columnas numéricas del CSV
feature_ids = []
for feature in feature_names:
    cur.execute("""
        INSERT INTO grafana_ml_model_feature (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, feature))
    feature_ids.append(cur.fetchone()[0])  # Guardamos el ID de la característica insertada

# Insertar los puntos (instancias) en la tabla grafana_ml_model_point
point_ids = []
for i in range(data_imputed.shape[0]):
    cur.execute("""
        INSERT INTO grafana_ml_model_point (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, f"point_{i}"))
    point_ids.append(cur.fetchone()[0])  # Guardamos el ID del punto insertado

# Insertar los valores en la tabla grafana_ml_model_point_value
for i in range(data_imputed.shape[0]):
    for j in range(data_imputed.shape[1]):
        cur.execute("""
            INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
            VALUES (%s, %s, %s, %s)
        """, (index_id, point_ids[i], feature_ids[j], float(data_imputed.iloc[i, j])))  # Convertimos a tipo Python nativo

# Confirmar los cambios en la base de datos
conn.commit()

# Cerrar el cursor y la conexión
cur.close()
conn.close()

print("Datos insertados correctamente en la base de datos.")
