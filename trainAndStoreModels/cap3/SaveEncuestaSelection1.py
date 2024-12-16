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
file_path = "/home/rolando/Kathy-Escuela/ML/csv/caso-Hoteles.csv"
data = pd.read_csv(file_path)

# Verificar los primeros registros de los datos cargados
print("Datos cargados:")
print(data.head())

# Filtrar las filas con 'polo' igual a 'Varadero'
data = data[data['polo'] == 'Varadero']

# Eliminar filas con valores nulos
data = data.dropna()

# Seleccionar solo las columnas requeridas
selected_columns = ['excelente', 'val_h', 'l_comentario', 'val_llm']
data_selected = data[selected_columns]

# Verificar los primeros registros de los datos seleccionados
print("\nDatos seleccionados:")
print(data_selected.head())

# Verificar si hay valores nulos en los datos seleccionados
print("\nComprobando si hay valores nulos en los datos seleccionados:")
print(data_selected.isnull().sum())

# Identificar las columnas de tipo objeto (posiblemente nominales)
nominal_columns = data_selected.select_dtypes(include=['object']).columns
print(f"\nColumnas nominales identificadas: {nominal_columns}")

# Convertir variables nominales en variables numéricas usando One Hot Encoding
data_encoded = pd.get_dummies(data_selected, columns=nominal_columns)
print("\nDatos después de aplicar One Hot Encoding:")
print(data_encoded.head())

# Verificar si hay valores nulos en los datos codificados
print("\nComprobando si hay valores nulos en los datos codificados:")
print(data_encoded.isnull().sum())

# Filtrar solo columnas numéricas (ahora incluirá las nuevas columnas codificadas)
data_encoded = data_encoded.select_dtypes(include=['number'])

# Verificar si alguna columna tiene solo valores NaN
print("\nComprobando columnas que contienen solo valores NaN:")
print(data_encoded.isna().sum())

# Eliminar columnas que contienen solo valores NaN
data_encoded = data_encoded.dropna(axis=1, how='all')
print("\nDatos después de eliminar columnas con solo NaN:")
print(data_encoded.head())

# Manejar valores NaN imputando con la media de cada columna
imputer = SimpleImputer(strategy='mean')
data_imputed = pd.DataFrame(imputer.fit_transform(data_encoded), columns=data_encoded.columns)

# Verificar si después de la imputación hay valores nulos
print("\nComprobando si hay valores nulos después de la imputación:")
print(data_imputed.isnull().sum())

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
print(f"\nID de la fila insertada en grafana_ml_model_index: {index_id}")

# Insertar los nombres de las características en la tabla grafana_ml_model_feature
feature_names = data_imputed.columns.tolist()  # Obtener los nombres de las columnas numéricas del CSV
feature_ids = []
for feature in feature_names:
    cur.execute("""
        INSERT INTO grafana_ml_model_feature (index, name) 
        VALUES (%s, %s) RETURNING id
    """, (index_id, feature))
    feature_ids.append(cur.fetchone()[0])  # Guardamos el ID de la característica insertada

# Imprimir los ID de las características insertadas
print("\nIDs de las características insertadas en grafana_ml_model_feature:")
print(feature_ids)

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

print("\nDatos insertados correctamente en la base de datos.")
