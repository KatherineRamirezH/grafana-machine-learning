import numpy as np
import psycopg2
import statsmodels.api as sm

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

    # Cargar las características de los puntos
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
        point_index = next(i for i, point in enumerate(points) if point[0] == v[0])  # Buscar el índice del punto
        feature_index = v[1] - values[0][1]  # Asegurarse de que el índice de las características sea correcto
        data[point_index, feature_index] = v[2]  # Asignar el valor al lugar adecuado

    # Cargar los nombres de las características
    cur.execute("""
        SELECT id, name
        FROM grafana_ml_model_feature
        WHERE index = %s
    """, (index,))
    feature_names = cur.fetchall()  # Cargar id y nombre de características

    cur.close()
    return data, feature_names, points


# Función para insertar los resultados de la regresión logística en la base de datos
def insert_logistic_regression_results(conn, index, feature_names, coefficients, p_values, std_errors):
    cur = conn.cursor()

    # Insertar el intercepto y su estadística z
    z_value_intercept = coefficients[0] / std_errors[0]  # Calcular z-score para el intercepto
    cur.execute("""
        INSERT INTO grafana_ml_model_regression (index, id_feature, coeff, p_value, value, std_err, type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (index, None, coefficients[0], p_values[0], z_value_intercept, std_errors[0], 'logistic'))

    # Insertar los resultados de los coeficientes, z-score, p-values y desviación estándar
    for i, (coef, p_value, std_err) in enumerate(zip(coefficients[1:], p_values[1:], std_errors[1:])):
        feature_id = feature_names[i][0]  # El id de la característica
        z_value = coef / std_err  # Calcular el z-score
        cur.execute("""
            INSERT INTO grafana_ml_model_regression (index, id_feature, coeff, p_value, value, std_err, type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (index, feature_id, coef, p_value, z_value, std_err, 'logistic'))

    conn.commit()
    cur.close()


# Función para realizar la regresión logística y almacenar los resultados
def logistic_regression_to_db(index, dbname, user='postgres', password='postgres', host='localhost', port='5432'):
    # Conectar a la base de datos
    conn = connect_to_db(dbname, user, password, host, port)

    # Cargar los datos desde la base de la base de datos
    data, feature_names, points = load_data_from_db(conn, index)

    # Dividir los datos en características y objetivo
    X = data[:, :-1]  # Características
    y = data[:, -1]   # Variable objetivo

    # Añadir columna de unos para el término independiente
    X = sm.add_constant(X)

    # Crear y ajustar el modelo de regresión logística
    model = sm.Logit(y, X)  # Modelo de regresión logística
    results = model.fit()

    # Extraer los resultados: coeficientes, p-values, desviación estándar
    coefficients = results.params  # Coeficientes del modelo
    p_values = results.pvalues  # P-values
    std_errors = results.bse  # Desviaciones estándar (errores estándar) de los coeficientes

    # Insertar los resultados en la base de datos
    insert_logistic_regression_results(conn, index, feature_names, coefficients, p_values, std_errors)

    # Cerrar la conexión
    conn.close()

    print(f"Resultados de la regresión logística insertados en la base de datos: '{dbname}'")


# Ejemplo de uso
if __name__ == "__main__":
    index = 4  # Este puede ser cualquier índice válido en tu base de datos

    # Llamar a la función de regresión logística y almacenamiento en base de datos
    logistic_regression_to_db(
        index=index,
        dbname='grafana_ml_model',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
