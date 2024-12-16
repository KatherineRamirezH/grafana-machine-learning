import psycopg2
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

# Crear datos aleatorios
num_points = 100  # Cantidad de puntos en el dataset
num_features = 5  # Número de características

# Generar datos aleatorios para las características y el target
X = np.random.rand(num_points, num_features)  # Características aleatorias
y = np.random.randint(0, 2, size=num_points)  # Target aleatorio (0 o 1)

# Definir nombres de las características
feature_names = [f"feature_{i}" for i in range(num_features)]

# Descripción y creador para grafana_ml_model_index
db_name = "Small Synthetic Dataset"
description = "Conjunto de datos sintético con 5 características y un target binario"
creator = "numpy"

# Insertar los datos en la tabla grafana_ml_model_index
cur.execute("""
    INSERT INTO grafana_ml_model_index (name, description, creator) 
    VALUES (%s, %s, %s) RETURNING id
""", (db_name, description, creator))

# Obtener el ID de la fila insertada
index_id = int(cur.fetchone()[0])

# Insertar los nombres de las características en la tabla grafana_ml_model_feature
feature_ids = []
for feature in feature_names:
    cur.execute("""
        INSERT INTO grafana_ml_model_feature (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (int(index_id), feature))
    feature_ids.append(int(cur.fetchone()[0]))

# Insertar la característica "target" en la tabla grafana_ml_model_feature
cur.execute("""
    INSERT INTO grafana_ml_model_feature (index, name) 
    VALUES (%s, %s) RETURNING id
""", (int(index_id), "target"))
target_feature_id = int(cur.fetchone()[0])

# Insertar los puntos (instancias) en la tabla grafana_ml_model_point
point_ids = []
for i in range(num_points):
    cur.execute("""
        INSERT INTO grafana_ml_model_point (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (int(index_id), f"point_{i}"))
    point_ids.append(int(cur.fetchone()[0]))

# Insertar los valores en la tabla grafana_ml_model_point_value
for i in range(num_points):
    # Insertar los valores de las características
    for j in range(num_features):
        cur.execute("""
            INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
            VALUES (%s, %s, %s, %s)
        """, (int(index_id), int(point_ids[i]), int(feature_ids[j]), float(X[i, j])))
    
    # Insertar el valor del target
    cur.execute("""
        INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
        VALUES (%s, %s, %s, %s)
    """, (int(index_id), int(point_ids[i]), int(target_feature_id), float(y[i])))

# Confirmar los cambios en la base de datos
conn.commit()

# Cerrar el cursor y la conexión
cur.close()
conn.close()

print("Datos insertados correctamente en la base de datos.")
