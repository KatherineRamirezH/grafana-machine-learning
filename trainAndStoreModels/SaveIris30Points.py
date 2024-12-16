import psycopg2
from sklearn.datasets import load_iris

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

# Cargar el dataset Iris
iris = load_iris()
X = iris.data[:25]  # Tomar solo las primeras 25 instancias
y = iris.target[:25]  # Etiquetas solo para las primeras 25 instancias
feature_names = iris.feature_names

# Descripción y creador para grafana_ml_model_index
db_name = "Iris 25 points"
description = "Subset del dataset Iris, que incluye un total de 25 muestras seleccionadas de las tres especies de flores (*Iris setosa*, *Iris versicolor* e *Iris virginica*). Contiene cuatro características numéricas: longitud y ancho de sépalo y pétalo."
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
    feature_ids.append(cur.fetchone()[0])

# Insertar los puntos (instancias) en la tabla grafana_ml_model_point
point_ids = []
for i in range(25):  # Insertar solo las primeras 25 instancias
    cur.execute("""
        INSERT INTO grafana_ml_model_point (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, f"point_{i}"))
    point_ids.append(cur.fetchone()[0])

# Insertar los valores en la tabla grafana_ml_model_point_value
for i in range(25):  # Solo para las primeras 25 instancias
    for j in range(X.shape[1]):  # Iterar sobre todas las características
        cur.execute("""
            INSERT INTO grafana_ml_model_point_value (index, id_point, id_feature, value) 
            VALUES (%s, %s, %s, %s)
        """, (index_id, point_ids[i], feature_ids[j], X[i, j]))

# Confirmar los cambios en la base de datos
conn.commit()

# Cerrar el cursor y la conexión
cur.close()
conn.close()

print("25 instancias insertadas correctamente en la base de datos.")
