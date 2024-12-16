import numpy as np
import psycopg2
import statsmodels.api as sm
from scipy.stats import t  # Para el cálculo del p-valor P>|t|

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


# Función para insertar los resultados de la regresión en la base de datos
def insert_regression_results(conn, index, feature_names, coefficients, std_errs, p_values, t_values):
    cur = conn.cursor()

    # Insertar el intercepto (primer coeficiente, correspondiente al término constante) con id_feature NULL
    cur.execute("""
        INSERT INTO grafana_ml_model_regression (index, id_feature, coeff, std_err, value, p_value, type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (index, None, coefficients[0], std_errs[0], t_values[0], p_values[0], 'linear'))

    # Insertar los coeficientes y resultados de las características
    for i, (coef, std_err, p_value, t_value) in enumerate(zip(coefficients[1:], std_errs[1:], p_values[1:], t_values[1:])):
        # Obtener el id_feature de la tabla grafana_ml_model_feature
        feature_id = feature_names[i][0]  # El id de la característica
        # Insertar el resultado de la regresión (coeficiente, desviación estándar, t-valor, p-valor)
        cur.execute("""
            INSERT INTO grafana_ml_model_regression (index, id_feature, coeff, std_err, value, p_value, type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (index, feature_id, coef, std_err, t_value, p_value, 'linear'))

    conn.commit()
    cur.close()


# Función para realizar la regresión lineal y almacenar los resultados
def linear_regression_to_db(index, dbname, user='postgres', password='postgres', host='localhost', port='5432'):
    # Conectar a la base de datos
    conn = connect_to_db(dbname, user, password, host, port)
    
    # Cargar los datos desde la base de la base de datos
    data, feature_names, points = load_data_from_db(conn, index)
    
    # Supongamos que la última columna es el objetivo (y) y el resto son las características (X)
    X = data[:, :-1]  # Características (todas excepto la última columna)
    y = data[:, -1]   # Objetivo (última columna)

    # Añadir una columna de unos a X para el término independiente (intercepto)
    X = sm.add_constant(X)

    # Realizar la regresión lineal usando statsmodels
    model = sm.OLS(y, X)  # Ordinary Least Squares (Mínimos cuadrados ordinarios)
    results = model.fit()

    # Extraer los resultados de la regresión
    coefficients = results.params  # Coeficientes (incluyendo el intercepto)
    std_errs = results.bse  # Desviaciones estándar de los coeficientes
    # Calcular t-values
    t_values = coefficients / std_errs  # Fórmula: t = coef / std_err
    # Calcular p-values P>|t|
    p_values = 2 * (1 - t.cdf(np.abs(t_values), df=len(y) - 1))  # Dos colas

    # Insertar los resultados de la regresión en la base de datos
    insert_regression_results(conn, index, feature_names, coefficients, std_errs, p_values, t_values)

    # Cerrar la conexión
    conn.close()

    print(f"Resultados de la regresión lineal insertados en la base de datos: '{dbname}'")


# Ejemplo de uso
if __name__ == "__main__":
    index = 3  # Este puede ser cualquier índice válido en tu base de datos

    # Llamar a la función de regresión lineal y almacenamiento en base de datos
    linear_regression_to_db(
        index=index,
        dbname='grafana_ml_model',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
