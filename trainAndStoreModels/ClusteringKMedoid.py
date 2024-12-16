import numpy as np
import psycopg2
from sklearn_extra.cluster import KMedoids
from sklearn.metrics import silhouette_score, davies_bouldin_score

# Función para conectar a la base de datos
def connect_to_db(dbname='grafana_ml_model', user='postgres', password='postgres', host='localhost', port='5432'):
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

    # Cargar los puntos
    cur.execute("""
        SELECT id
        FROM grafana_ml_model_point
        WHERE index = %s
    """, (index,))
    points = cur.fetchall()

    # Cargar las características de los puntos
    cur.execute("""
        SELECT id_point, id_feature, value
        FROM grafana_ml_model_point_value
        WHERE index = %s
    """, (index,))
    values = cur.fetchall()

    # Organizar los datos en una matriz
    num_points = len(points)
    num_features = len(set([v[1] for v in values]))
    data = np.zeros((num_points, num_features))

    for v in values:
        point_index = next(i for i, point in enumerate(points) if point[0] == v[0])
        feature_index = v[1] - values[0][1]
        data[point_index, feature_index] = v[2]

    cur.close()
    return data, points


# Insertar los clústeres en la tabla grafana_ml_model_cluster con sus métricas
def insert_cluster_data(conn, index, clusters, data, kmedoids):
    cur = conn.cursor()
    cluster_ids = []

    for i in set(clusters):
        # Crear máscara para identificar los puntos de este clúster
        cluster_mask = clusters == i
        cluster_points = data[cluster_mask]
      
        silhouette_cluster = silhouette_score(data, clusters == i)
        davies_bouldin_cluster = davies_bouldin_score(data, clusters == i)

        # Calcular inercia para el clúster
        cluster_center = data[kmedoids.medoid_indices_[i]]
        inertia_cluster = np.sum(np.abs(np.linalg.norm(cluster_points - cluster_center, axis=1)))

        # Insertar en la base de datos
        cur.execute("""
            INSERT INTO grafana_ml_model_cluster (index, number, inertia, silhoutte_coefficient, davies_bouldin_index)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (index, int(i), inertia_cluster, silhouette_cluster, davies_bouldin_cluster))

        cluster_ids.append(cur.fetchone()[0])

    conn.commit()
    cur.close()
    return cluster_ids


# Insertar los puntos en sus clústeres
def insert_point_cluster_data(conn, index, points, clusters, cluster_ids, kmedoids):
    cur = conn.cursor()

    # Insertar los puntos en la tabla de puntos-clúster
    for i, cluster in enumerate(clusters):
        point_id = int(points[i][0])
        cluster_id = cluster_ids[cluster]
        
        # Determinar si el punto es un centro de clúster (medoide)
        is_center = True if i in kmedoids.medoid_indices_ else False
        
        # Insertar los datos en la base de datos
        cur.execute("""
            INSERT INTO grafana_ml_model_point_kmedoids (index, id_point, id_cluster, is_medoid)
            VALUES (%s, %s, %s, %s)
        """, (index, point_id, cluster_id, is_center))

    conn.commit()
    cur.close()


# Insertar las métricas generales del agrupamiento en la tabla grafana_ml_model_metrics_clustering
def insert_clustering_metrics(conn, index, inertia, silhouette, davies_bouldin):
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO grafana_ml_model_metrics_clustering (index, type, inertia, silhoutte_coefficient, davies_bouldin_index)
        VALUES (%s, %s, %s, %s, %s)
    """, (index, 'KMedoids', inertia, silhouette, davies_bouldin))

    conn.commit()
    cur.close()


# Función para realizar el agrupamiento K-Medoids y almacenar en la base de datos
def kmedoids_clustering_to_db(index, dbname, user='postgres', password='postgres', host='localhost', port='5432', k=3):
    # Conectar a la base de datos
    conn = connect_to_db(dbname, user, password, host, port)

    # Cargar los datos desde la base de datos
    data, points = load_data_from_db(conn, index)

    # Realizar el agrupamiento K-Medoids
    kmedoids = KMedoids(n_clusters=k, random_state=42)
    clusters = kmedoids.fit_predict(data)

    # Insertar los clústeres en la tabla de clústeres con sus métricas
    cluster_ids = insert_cluster_data(conn, index, clusters, data, kmedoids)

    # Insertar los puntos en la tabla grafana_ml_model_point_kmedoid
    insert_point_cluster_data(conn, index, points, clusters, cluster_ids, kmedoids)

    # Insertar las métricas generales del agrupamiento
    inertia = kmedoids.inertia_
    silhouette = silhouette_score(data, clusters)
    davies_bouldin = davies_bouldin_score(data, clusters)

    insert_clustering_metrics(conn, index, inertia, silhouette, davies_bouldin)

    # Cerrar la conexión
    conn.close()

    print(f"Datos de agrupamiento K-Medoids insertados en la base de datos: '{dbname}'")


# Ejemplo de uso
if __name__ == "__main__":
    index = 4  # Índice de la base de datos a analizar

    # Llamar a la función de agrupamiento K-Medoids y almacenamiento en base de datos
    kmedoids_clustering_to_db(
        index=index,
        dbname='grafana_ml_model',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432',
        k=3  # Número de clústeres
    )
