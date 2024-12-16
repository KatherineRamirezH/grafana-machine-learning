from sklearn.datasets import load_wine
import psycopg2
import pandas as pd

# Cargar el dataset Wine de scikit-learn
wine = load_wine()
wine_data = pd.DataFrame(wine.data, columns=wine.feature_names)
wine_data['target'] = wine.target  # Agregamos la variable objetivo (target) a la base de datos

# Conectar a la base de datos PostgreSQL
conn = psycopg2.connect(
    dbname="grafana_ml_model", 
    user="postgres", 
    password="postgres", 
    host="localhost", 
    port="5432"
)

# Crear un cursor
cur = conn.cursor()

# Descripción para la base de datos
db_name = "Wine"
description = "Dataset de características físico-químicas de diferentes variedades de vino. Incluye medidas como acidez, pH, contenido de azúcares y alcohol, entre otras, obtenidas a partir de muestras químicas. Este conjunto de datos permite analizar diferencias entre variedades y estudiar relaciones entre sus propiedades."
creator = "Scikit-learn"

# Insertar los datos en la tabla de índice
cur.execute("""
    INSERT INTO grafana_ml_model_index (name, description, creator) 
    VALUES (%s, %s, %s) RETURNING id
""", (db_name, description, creator))
index_id = cur.fetchone()[0]

# Insertar nombres de las características en la base de datos
feature_ids = []
for feature in wine.feature_names:
    cur.execute("""
        INSERT INTO grafana_ml_model_feature (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, feature))
    feature_ids.append(cur.fetchone()[0])

# Insertar las instancias en la base de datos
point_ids = []
for i in range(len(wine_data)):
    cur.execute("""
        INSERT INTO grafana_ml_model_point (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, f"point_{i}"))
    point_ids.append(cur.fetchone()[0])

# Insertar los valores en la base de datos
for i in range(len(wine_data)):
    for j, feature_id in enumerate(feature_ids):
        cur.execute("""
            INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
            VALUES (%s, %s, %s, %s)
        """, (index_id, point_ids[i], feature_id, wine_data.iloc[i, j]))

# Confirmar los cambios en la base de datos
conn.commit()

# Cerrar el cursor y la conexión
cur.close()
conn.close()

print("Datos del dataset Wine Dataset insertados correctamente en la base de datos.")
