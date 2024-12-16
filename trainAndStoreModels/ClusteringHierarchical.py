import numpy as np
import psycopg2
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
import matplotlib.pyplot as plt
from psycopg2 import sql

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
    num_features = len(set([v[1] for v in values]))
    data = np.zeros((num_points, num_features))  # Matriz de datos de características

    # Mapear el ID de los puntos a índices en la matriz de datos
    point_id_to_index = {point[0]: i for i, point in enumerate(points)}  # Crear un mapeo de IDs reales a índices

    # Llenar la matriz de datos con los valores
    for v in values:
        point_index = point_id_to_index.get(v[0])  # Mapear el ID real al índice
        feature_index = v[1] - values[0][1]  # Índice de las características
        if feature_index >= 0 and feature_index < data.shape[1]:
            data[point_index, feature_index] = v[2]  # Asignar el valor al lugar adecuado

    # Cargar los nombres de las características
    cur.execute("""
        SELECT name
        FROM grafana_ml_model_feature
        WHERE index = %s
    """, (index,))
    feature_names = [row[0] for row in cur.fetchall()]

    cur.close()
    return data, feature_names, points, [point[0] for point in points]  # Devuelve también los IDs originales


# Insertar los puntos iniciales en la base de datos
def insert_point_data(conn, data, index, original_ids):
    cur = conn.cursor()
    node_id_map = {}
    
    # Iterar sobre los puntos usando sus IDs reales
    for i, point_id in enumerate(original_ids):
        cur.execute("""
            INSERT INTO grafana_ml_model_hierarchical_clustering ("index", id_parent, id_point, name, height)
            VALUES (%s, NULL, %s, %s, 0) RETURNING id
        """, (index, point_id, f'Point {i+1}'))  # Aquí utilizamos el ID real del punto de la base de datos
        
        node_id_map[i] = cur.fetchone()[0]  # Mapear el índice al nuevo nodo
    conn.commit()
    cur.close()
    
    return node_id_map


# Insertar los nodos del árbol jerárquico (sin `number_cluster` en los nodos)
def insert_cluster_data(conn, Z, node_id_map, k, index):
    cur = conn.cursor()
    for i, (left, right, dist, _) in enumerate(Z):
        left_id = node_id_map[int(left)]
        right_id = node_id_map[int(right)]

        # Calcular la altura como la distancia de fusión
        height = dist

        # Insertar el nuevo nodo que es el padre de los nodos fusionados
        cur.execute("""
        INSERT INTO grafana_ml_model_hierarchical_clustering ("index", id_parent, name, height)
        VALUES (%s, %s, %s, %s) RETURNING id
        """, (index, None, f'Cluster {len(node_id_map) + 1}', height))
        parent_id = cur.fetchone()[0]
        node_id_map[len(node_id_map)] = parent_id  # Agregar al mapa

        # Actualizar los nodos hijos con el nuevo padre
        cur.execute(f"UPDATE grafana_ml_model_hierarchical_clustering SET id_parent = %s WHERE id = %s", (parent_id, left_id))
        cur.execute(f"UPDATE grafana_ml_model_hierarchical_clustering SET id_parent = %s WHERE id = %s", (parent_id, right_id))

    conn.commit()
    cur.close()


# Realizar el agrupamiento jerárquico y guardar los resultados en la base de datos
def hierarchical_clustering_to_db(index, dbname, user='postgres', password='postgres', host='localhost', port='5432', 
                                  k=3, method='ward', linkage_metric='euclidean', visualize=True):
    conn = connect_to_db(dbname, user, password, host, port)

    # Cargar los datos desde la base de datos
    data, feature_names, points, original_ids = load_data_from_db(conn, index)

    # Realizar el agrupamiento jerárquico
    Z = linkage(data, method=method, metric=linkage_metric)

    # Insertar los puntos en la base de datos
    node_id_map = insert_point_data(conn, data, index, original_ids)

    # Insertar los nodos del árbol jerárquico
    insert_cluster_data(conn, Z, node_id_map, k, index)

    conn.close()
    print(f"Datos de agrupamiento jerárquico insertados en la base de datos: '{dbname}'")

    # Visualizar el dendrograma
    if visualize:
        plt.figure(figsize=(10, 7))
        dendrogram(Z, labels=[f'Point {i+1}' for i in range(len(data))], leaf_rotation=0)
        plt.title('Dendrograma del Agrupamiento Jerárquico')
        plt.xlabel('Puntos')
        plt.ylabel('Distancia')
        plt.show()

# Ejemplo de uso
if __name__ == "__main__":
    hierarchical_clustering_to_db(
        index=5,  # Índice para la base de datos
        dbname='grafana_ml_model',  # Nombre de la base de datos
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432',
        k=3,  # Número de clústeres
        method='ward',
        linkage_metric='euclidean',
        visualize=True
    )
