import psycopg2
from sklearn.datasets import load_diabetes

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

# Cargar el dataset de diabetes
diabetes = load_diabetes()
X = diabetes.data
y = diabetes.target
feature_names = diabetes.feature_names

# Descripción y creador para grafana_ml_model_index
db_name = "Diabetes"
description = "Dataset de diabetes que contiene información clínica y fisiológica de 442 pacientes. Incluye 10 características numéricas como edad, índice de masa corporal (IMC), presión arterial y mediciones bioquímicas obtenidas a partir de análisis sanguíneos. El objetivo es predecir una variable continua que mide la progresión de la diabetes un año después de la recolección de los datos."
creator = "scikit-learn"

# Insertar los datos en la tabla grafana_ml_model_index
cur.execute("""
    INSERT INTO grafana_ml_model_index (name, description, creator) 
    VALUES (%s, %s, %s) RETURNING id
""", (db_name, description, creator))

# Obtener el ID de la fila insertada
index_id = cur.fetchone()[0]

# Insertar los nombres de las características en la tabla grafana_ml_model_feature
# Guardamos los IDs generados de las características
feature_ids = []
for feature in feature_names:
    cur.execute("""
        INSERT INTO grafana_ml_model_feature (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, feature))  # PostgreSQL generará el ID automáticamente
    feature_ids.append(cur.fetchone()[0])  # Guardamos el ID de la característica insertada

# Insertar la característica "target" en la tabla grafana_ml_model_feature
cur.execute("""
    INSERT INTO grafana_ml_model_feature (index, name) 
    VALUES (%s, %s) RETURNING id
""", (index_id, "target"))  # Insertamos "target" como una nueva característica
target_feature_id = cur.fetchone()[0]  # Guardamos el ID de la característica "target"

# Insertar los puntos (instancias) en la tabla grafana_ml_model_point
# Guardamos los IDs generados de los puntos
point_ids = []
for i in range(X.shape[0]):
    cur.execute("""
        INSERT INTO grafana_ml_model_point (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, f"point_{i}"))  # PostgreSQL generará el ID automáticamente
    point_ids.append(cur.fetchone()[0])  # Guardamos el ID del punto insertado

# Insertar los valores en la tabla grafana_ml_model_point_value
for i in range(X.shape[0]):
    # Insertar los valores de las características X originales
    for j in range(X.shape[1]):
        cur.execute("""
            INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
            VALUES (%s, %s, %s, %s)
        """, (index_id, point_ids[i], feature_ids[j], X[i, j]))  # Usamos los IDs guardados para insertar
    
    # Insertar el valor de la característica "target" para cada punto
    cur.execute("""
        INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
        VALUES (%s, %s, %s, %s)
    """, (index_id, point_ids[i], target_feature_id, y[i]))  # Asociamos el valor de "target" al punto

# Confirmar los cambios en la base de datos
conn.commit()

# Cerrar el cursor y la conexión
cur.close()
conn.close()

print("Datos insertados correctamente en la base de datos.")
