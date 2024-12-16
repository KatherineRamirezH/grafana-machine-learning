import numpy as np
import psycopg2
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, pairwise_distances, silhouette_samples

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

    # Cargar las características de los puntos (iris)
    cur.execute("""
        SELECT id, name
        FROM grafana_ml_model_point
        WHERE index = %s
    """, (index,))
    points = cur.fetchall()  # Los IDs y nombres de los puntos

    # Cargar los valores de las características de los puntos
    cur.execute("""
        SELECT id_point, id_feature, value
        FROM grafana_ml_model_point_value
        WHERE index = %s
    """, (index,))
    values = cur.fetchall()  # Los valores de características (id_point, id_feature, value)

    # Organizar los datos en un formato adecuado
    num_points = len(points)
    num_features = len(set([v[1] for v in values]))  # Identificar el número de características
    data = np.zeros((num_points, num_features))  # Matriz de datos de características

    # Llenar la matriz de datos con los valores
    for v in values:
        # v[0] -> id_point
        # v[1] -> id_feature
        # v[2] -> value
        point_index = next(i for i, point in enumerate(points) if point[0] == v[0])  # Buscar el índice del punto
        feature_index = v[1] - values[0][1]  # Asegurarse de que el índice de las características sea correcto
        data[point_index, feature_index] = v[2]  # Asignar el valor al lugar adecuado

    # Cargar los nombres de las características
    cur.execute("""
        SELECT name
        FROM grafana_ml_model_feature
        WHERE index = %s
    """, (index,))
    feature_names = [row[0] for row in cur.fetchall()]

    cur.close()
    return data, feature_names, points

# Insertar los clústeres en la tabla grafana_ml_model_cluster con sus métricas
def insert_cluster_data(conn, index, clusters, data, kmeans):
    cur = conn.cursor()
    cluster_ids = []

    for i in set(clusters):
        # Convertir `i` a int para evitar el error
        cluster_mask = clusters == i
        cluster_points = data[cluster_mask]
 
        # Calcular métricas individuales
        silhouette_cluster = silhouette_score(data, clusters == i)
        davies_bouldin_cluster = davies_bouldin_score(data, clusters == i)

        # Calcular inercia para el clúster
        cluster_center = kmeans.cluster_centers_[i]
        inertia_cluster = np.sum(np.linalg.norm(cluster_points - cluster_center, axis=1) ** 2)

        # Insertar en la base de datos
        cur.execute("""
            INSERT INTO grafana_ml_model_cluster (index, number, inertia, silhoutte_coefficient, davies_bouldin_index)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (index, int(i), inertia_cluster, silhouette_cluster, davies_bouldin_cluster))  # Conversión aquí

        cluster_ids.append(cur.fetchone()[0])  # Obtener el id del cluster insertado

    conn.commit()
    cur.close()
    return cluster_ids

# Insertar los puntos y los centroides en la tabla grafana_ml_model_point_cluster
def insert_point_cluster_data(conn, index, points, clusters, cluster_ids):
    cur = conn.cursor()

    # Insertar los puntos en la tabla de puntos-clúster
    for i, cluster in enumerate(clusters):
        point_id = int(points[i][0])  # Convertimos a int para evitar el error de tipo
        cluster_id = cluster_ids[cluster]  # Usar el ID del cluster insertado
        cur.execute("""
            INSERT INTO grafana_ml_model_point_kmeans (index, id_point, id_cluster)
            VALUES (%s, %s, %s)
        """, (index, point_id, cluster_id))  # Usamos False para is_center porque son puntos

    conn.commit()
    cur.close()

# Insertar los centroides en la tabla grafana_ml_model_centroid
def insert_centroids_to_db(conn, index, centroids, feature_names, cluster_ids):
    cur = conn.cursor()
    
    # Obtener los IDs de las características en el orden correspondiente
    cur.execute("""
        SELECT id, name
        FROM grafana_ml_model_feature
        WHERE index = %s
        ORDER BY id
    """, (index,))
    features = {row[1]: row[0] for row in cur.fetchall()}  # Mapeamos name -> id

    for i, centroid in enumerate(centroids):
        for j, value in enumerate(centroid):
            feature_name = feature_names[j]
            id_feature = features[feature_name]  # Buscar el ID correcto basado en el nombre
            
            cur.execute("""
                INSERT INTO grafana_ml_model_centroid (index, id_cluster, id_feature, value)
                VALUES (%s, %s, %s, %s)
            """, (index, cluster_ids[i], id_feature, value))

    conn.commit()
    cur.close()
# Insertar las métricas generales del agrupamiento en la tabla grafana_ml_model_metrics_clustering
def insert_clustering_metrics(conn, index, inertia, silhouette, davies_bouldin):
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO grafana_ml_model_metrics_clustering (index, type, inertia, silhoutte_coefficient, davies_bouldin_index)
        VALUES (%s, %s, %s, %s, %s)
    """, (index, 'KMeans', inertia, silhouette, davies_bouldin))

    conn.commit()
    cur.close()

# Función para realizar el agrupamiento K-Means y almacenar en la base de datos
def kmeans_clustering_to_db(index, dbname, user='postgres', password='postgres', host='localhost', port='5432', k=3):
    # Conectar a la base de datos
    conn = connect_to_db(dbname, user, password, host, port)
    
    # Cargar los datos desde la base de datos
    data, feature_names, points = load_data_from_db(conn, index)
    
    # Realizar el agrupamiento K-Means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')  # Usamos 'auto' para evitar el warning
    clusters = kmeans.fit_predict(data)
    centroids = kmeans.cluster_centers_  # Centroides de los clústeres
    
    # Insertar los clústeres en la tabla de clústeres con sus métricas
    cluster_ids = insert_cluster_data(conn, index, clusters, data, kmeans)
    
    # Insertar los puntos en la tabla grafana_ml_model_point_cluster (sin centroides)
    insert_point_cluster_data(conn, index, points, clusters, cluster_ids)
    
    # Insertar los centroides en la tabla grafana_ml_model_centroid
    insert_centroids_to_db(conn, index, centroids, feature_names, cluster_ids)
    
    # Insertar las métricas generales del agrupamiento
    inertia = kmeans.inertia_
    silhouette = silhouette_score(data, clusters)
    davies_bouldin = davies_bouldin_score(data, clusters)
    
    insert_clustering_metrics(conn, index, inertia, silhouette, davies_bouldin)
    
    # Cerrar la conexión
    conn.close()

    print(f"Datos de agrupamiento K-Means insertados en la base de datos: '{dbname}'")

# Ejemplo de uso
if __name__ == "__main__":
    index = 4 # Índice de la base de datos a analizar

    # Llamar a la función de agrupamiento K-Means y almacenamiento en base de datos
    kmeans_clustering_to_db(
        index=index,
        dbname='grafana_ml_model',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432',
        k=3  # Número de clústeres
    )