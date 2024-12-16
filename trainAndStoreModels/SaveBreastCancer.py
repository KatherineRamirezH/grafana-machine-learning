import psycopg2
from sklearn.datasets import load_breast_cancer

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

# Cargar el dataset de cáncer de mama
cancer = load_breast_cancer()
X = cancer.data
y = cancer.target
feature_names = cancer.feature_names

# Descripción y creador para grafana_ml_model_index
db_name = "Breast Cancer"
description = "Dataset de cáncer de mama"
creator = "scikit-learn"

# Insertar los datos en la tabla grafana_ml_model_index
cur.execute("""
    INSERT INTO grafana_ml_model_index (name, description, creator) 
    VALUES (%s, %s, %s) RETURNING id
""", (db_name, description, creator))

# Obtener el ID de la fila insertada y convertirlo a int
index_id = int(cur.fetchone()[0])

# Insertar los nombres de las características en la tabla grafana_ml_model_feature
# Guardamos los IDs generados de las características
feature_ids = []
for feature in feature_names:
    cur.execute("""
        INSERT INTO grafana_ml_model_feature (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (int(index_id), feature))  # Convertir index_id a int
    feature_ids.append(int(cur.fetchone()[0]))  # Convertir a int y guardar el ID

# Insertar la característica "target" en la tabla grafana_ml_model_feature
cur.execute("""
    INSERT INTO grafana_ml_model_feature (index, name) 
    VALUES (%s, %s) RETURNING id
""", (int(index_id), "target"))  # Insertamos "target" como una nueva característica
target_feature_id = int(cur.fetchone()[0])  # Convertir a int el ID de la característica "target"

# Insertar los puntos (instancias) en la tabla grafana_ml_model_point
# Guardamos los IDs generados de los puntos
point_ids = []
for i in range(X.shape[0]):
    cur.execute("""
        INSERT INTO grafana_ml_model_point (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (int(index_id), f"point_{i}"))  # Convertir index_id a int
    point_ids.append(int(cur.fetchone()[0]))  # Convertir a int el ID de cada punto insertado

# Insertar los valores en la tabla grafana_ml_model_point_value
for i in range(X.shape[0]):
    # Insertar los valores de las características X originales
    for j in range(X.shape[1]):
        cur.execute("""
            INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
            VALUES (%s, %s, %s, %s)
        """, (int(index_id), int(point_ids[i]), int(feature_ids[j]), float(X[i, j])))  # Conversión a int/float según sea necesario
    
    # Insertar el valor de la característica "target" para cada punto
    cur.execute("""
        INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
        VALUES (%s, %s, %s, %s)
    """, (int(index_id), int(point_ids[i]), int(target_feature_id), float(y[i])))  # Conversión a int/float

# Confirmar los cambios en la base de datos
conn.commit()

# Cerrar el cursor y la conexión
cur.close()
conn.close()

print("Datos insertados correctamente en la base de datos.")
