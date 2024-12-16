import psycopg2
from sklearn.datasets import load_wine
import numpy as np

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

# Cargar el dataset Wine
wine = load_wine()
X = wine.data
y = wine.target
feature_names = wine.feature_names

# Reducir el dataset a 30 instancias
indices = np.random.choice(X.shape[0], size=30, replace=False)
X_subset = X[indices]
y_subset = y[indices]

# Descripción y creador para grafana_ml_model_index
db_name = "Wine"
description = "Conjunto de datos Wine reducido a 30 instancias para agrupamiento jerárquico"
creator = "scikit-learn"

# Insertar los datos en la tabla grafana_ml_model_index
cur.execute("""
    INSERT INTO grafana_ml_model_index (name, description, creator) 
    VALUES (%s, %s, %s) RETURNING id
""", (db_name, description, creator))

# Obtener el ID de la fila insertada
index_id = cur.fetchone()[0]

# Insertar los nombres de las características en la tabla grafana_ml_model_feature
feature_ids = []
for feature in feature_names:
    cur.execute("""
        INSERT INTO grafana_ml_model_feature (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, feature))
    
    # Obtener el id de la característica insertada
    feature_ids.append(cur.fetchone()[0])

# Insertar los puntos (instancias) en la tabla grafana_ml_model_point
point_ids = []
for i in range(X_subset.shape[0]):
    cur.execute("""
        INSERT INTO grafana_ml_model_point (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, f"point_{i}"))
    
    # Obtener el id del punto insertado
    point_ids.append(cur.fetchone()[0])

# Insertar los valores en la tabla grafana_ml_model_point_value
for i in range(X_subset.shape[0]):
    for j in range(X_subset.shape[1]):
        cur.execute("""
            INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
            VALUES (%s, %s, %s, %s)
        """, (index_id, point_ids[i], feature_ids[j], X_subset[i, j]))  # Usamos los IDs previamente guardados

# Confirmar los cambios en la base de datos
conn.commit()

# Cerrar el cursor y la conexión
cur.close()
conn.close()

print("Datos insertados correctamente en la base de datos.")
