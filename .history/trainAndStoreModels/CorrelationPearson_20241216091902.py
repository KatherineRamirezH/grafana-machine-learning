import numpy as np
import psycopg2
import scipy.stats as stats  # Importamos la biblioteca scipy.stats

# Función para conectar a la base de datos
def connect_to_db(dbname, user='postgres', password='postgres', host='localhost', port='5432'):
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return None

# Función para cargar los datos de la base de datos
def load_data_from_db(conn, index):
    cur = conn.cursor()

    # Cargar los valores de las características de los puntos
    cur.execute("""
        SELECT id_point, id_feature, value
        FROM grafana_ml_model_point_value
        WHERE index = %s
    """, (index,))
    values = cur.fetchall()  # Los valores de características (id_point, id_feature, value)

    # Organizar los datos en un formato adecuado
    point_ids = set(v[0] for v in values)  # Extraer los id de los puntos
    feature_ids = set(v[1] for v in values)  # Extraer los id de las características
    
    num_points = len(point_ids)  # El número de puntos únicos
    num_features = len(feature_ids)  # El número de características únicas
    
    data = np.zeros((num_points, num_features))  # Matriz de datos de características
    feature_ids_map = {}  # Diccionario para almacenar los ids de las características

    # Crear un mapeo de id_point y id_feature a índices
    point_index_map = {pid: idx for idx, pid in enumerate(sorted(point_ids))}
    feature_index_map = {fid: idx for idx, fid in enumerate(sorted(feature_ids))}

    # Llenar la matriz de datos con los valores
    for v in values:
        point_index = point_index_map[v[0]]  # Mapear el id_point a un índice
        feature_index = feature_index_map[v[1]]  # Mapear el id_feature a un índice
        data[point_index, feature_index] = v[2]  # Asignar el valor al lugar adecuado
        feature_ids_map[feature_index] = v[1]  # Asociar el índice con el id de la característica

    # Cargar los nombres de las características
    cur.execute("""
        SELECT id, name
        FROM grafana_ml_model_feature
        WHERE index = %s
    """, (index,))
    feature_names = {row[0]: row[1] for row in cur.fetchall()}  # Diccionario con id_feature y name

    cur.close()
    return data, feature_names, feature_ids_map

# Función para calcular la correlación de Pearson utilizando scipy
def pearson_correlation(data):
    num_features = data.shape[1]
    correlations = []
    
    for i in range(num_features):
        for j in range(i + 1, num_features):  # No repetir correlaciones (i, j) y (j, i)
            corr, _ = stats.pearsonr(data[:, i], data[:, j])  # Calcula la correlación de Pearson
            correlations.append((i + 1, j + 1, corr))  # Almacenamos los índices y el valor de la correlación
    
    return correlations

# Función para insertar la correlación de Pearson en la base de datos
def insert_pearson_correlation(conn, index, correlations, feature_ids):
    cur = conn.cursor()
    for feature1, feature2, corr_value in correlations:
        id_feature1 = feature_ids[feature1 - 1]  # Obtener el ID de la primera característica
        id_feature2 = feature_ids[feature2 - 1]  # Obtener el ID de la segunda característica
        cur.execute("""
            INSERT INTO grafana_ml_model_correlation (index, id_feature1, id_feature2, value, type)
            VALUES (%s, %s, %s, %s, 'pearson')
        """, (index, id_feature1, id_feature2, corr_value))
    
    conn.commit()
    cur.close()

# Función para calcular y almacenar las correlaciones de Pearson en la base de datos
def pearson_correlation_to_db(index, dbname, user='postgres', password='postgres', host='localhost', port='5432'):
    # Conectar a la base de datos
    conn = connect_to_db(dbname, user, password, host, port)
    
    # Cargar los datos desde la base de datos
    data, feature_names, feature_ids = load_data_from_db(conn, index)
    
    # Calcular las correlaciones de Pearson
    correlations = pearson_correlation(data)
    
    # Insertar las correlaciones en la base de datos
    insert_pearson_correlation(conn, index, correlations, feature_ids)
    
    # Cerrar la conexión
    conn.close()

    print(f"Correlaciones de Pearson insertadas en la base de datos: '{dbname}'")

# Ejemplo de uso
if __name__ == "__main__":
    index = 3  # Este puede ser cualquier índice válido en tu base de datos

    # Llamar a la función de correlación de Pearson y almacenamiento en base de datos
    pearson_correlation_to_db(
        index=index,
        dbname='grafana_ml_model',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
