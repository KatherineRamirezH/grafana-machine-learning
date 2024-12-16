import pandas as pd

# Cargar el archivo CSV
df = pd.read_csv("/home/rolando/Kathy-Escuela/ML/csv/caso-Hoteles.csv")

# Contar valores nulos por columna
print("Cantidad de valores nulos por columna:")
print(df.isnull().sum())

# Opcional: Filtrar columnas que tienen valores nulos
nulos = df.isnull().sum()
columnas_con_nulos = nulos[nulos > 0]
print("\nColumnas con valores nulos:")
print(columnas_con_nulos)

# Obtener un resumen general
print("\nResumen general del DataFrame:")
print(df.describe(include='all'))

# Contar valores únicos por columna
print("\nConteo de valores únicos por columna:")
for column in df.columns:
    print(f"Resumen de la columna '{column}':")
    print(df[column].value_counts(dropna=False))  # Incluye los valores nulos en el conteo
    print(f"Número total de valores únicos: {df[column].nunique(dropna=True)}")  # Excluye los nulos
    print()

# Cantidad inicial de filas
filas_iniciales = df.shape[0]
print(f"Cantidad inicial de filas: {filas_iniciales}")

# Eliminar filas con valores nulos
df_sin_nulos = df.dropna()

# Cantidad de filas restantes
filas_restantes = df_sin_nulos.shape[0]
print(f"Cantidad de filas después de eliminar los valores nulos: {filas_restantes}")

# Cantidad de filas eliminadas
filas_eliminadas = filas_iniciales - filas_restantes
print(f"Cantidad de filas eliminadas: {filas_eliminadas}")