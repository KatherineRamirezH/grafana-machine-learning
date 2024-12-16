CREATE TABLE "grafana_ml_model_index" (
  "id" SERIAL PRIMARY KEY,
  "name" TEXT,
  "description" TEXT,
  "creator" TEXT
);

CREATE TABLE "grafana_ml_model_feature" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "name" TEXT
);

CREATE TABLE "grafana_ml_model_point" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "name" TEXT
);

CREATE TABLE "grafana_ml_model_point_value" (
  "index" INTEGER,
  "id_point" INTEGER,
  "id_feature" INTEGER,
  "value" DOUBLE PRECISION,
  PRIMARY KEY ("id_point", "id_feature")
);

CREATE TABLE "grafana_ml_model_correlation" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "id_feature1" INTEGER,
  "id_feature2" INTEGER,
  "value" DOUBLE PRECISION,
  "type" TEXT
);

CREATE TABLE "grafana_ml_model_regression" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "id_feature" INTEGER,
  "coeff" DOUBLE PRECISION,
  "std_err" DOUBLE PRECISION,
  "value" DOUBLE PRECISION,
  "p_value" DOUBLE PRECISION,
  "type" TEXT
);

CREATE TABLE "grafana_ml_model_point_kmeans" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "id_point" INTEGER,
  "id_cluster" INTEGER
);

CREATE TABLE "grafana_ml_model_point_kmedoids" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "id_point" INTEGER,
  "is_medoid" BOOLEAN,
  "id_cluster" INTEGER
);

CREATE TABLE "grafana_ml_model_cluster" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "number" INTEGER,
  "inertia" DOUBLE PRECISION,
  "silhoutte_coefficient" DOUBLE PRECISION,
  "davies_bouldin_index" DOUBLE PRECISION
);

CREATE TABLE "grafana_ml_model_centroid" (
    "index" INTEGER,
    "id_cluster" INTEGER,
    "id_feature" INTEGER,
    "value" DOUBLE PRECISION
);

CREATE TABLE "grafana_ml_model_metrics_clustering" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "type" TEXT,
  "inertia" DOUBLE PRECISION,
  "silhoutte_coefficient" DOUBLE PRECISION,
  "davies_bouldin_index" DOUBLE PRECISION
);

CREATE TABLE "grafana_ml_model_hierarchical_clustering" (
  "index" INTEGER,
  "id" SERIAL PRIMARY KEY,
  "id_parent" INTEGER,
  "id_point" INTEGER,
  "name" TEXT,
  "height" DOUBLE PRECISION
);



ALTER TABLE "grafana_ml_model_feature" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_point" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_point_value" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_correlation" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_regression" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_point_kmeans" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_point_kmedoids" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_centroid" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_cluster" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_metrics_clustering" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_hierarchical_clustering" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");



ALTER TABLE "grafana_ml_model_regression" ADD FOREIGN KEY ("id_feature") REFERENCES "grafana_ml_model_feature" ("id");

ALTER TABLE "grafana_ml_model_correlation" ADD FOREIGN KEY ("id_feature1") REFERENCES "grafana_ml_model_feature" ("id");

ALTER TABLE "grafana_ml_model_correlation" ADD FOREIGN KEY ("id_feature2") REFERENCES "grafana_ml_model_feature" ("id");

ALTER TABLE "grafana_ml_model_point_value" ADD FOREIGN KEY ("id_point") REFERENCES "grafana_ml_model_point" ("id");

ALTER TABLE "grafana_ml_model_point_value" ADD FOREIGN KEY ("id_feature") REFERENCES "grafana_ml_model_feature" ("id");

ALTER TABLE "grafana_ml_model_hierarchical_clustering" ADD FOREIGN KEY ("id_parent") REFERENCES "grafana_ml_model_hierarchical_clustering" ("id");

ALTER TABLE "grafana_ml_model_point_kmeans" ADD FOREIGN KEY ("id_cluster") REFERENCES "grafana_ml_model_cluster" ("id");

ALTER TABLE "grafana_ml_model_point_kmeans" ADD FOREIGN KEY ("id_point") REFERENCES "grafana_ml_model_point" ("id");

ALTER TABLE "grafana_ml_model_point_kmedoids" ADD FOREIGN KEY ("id_cluster") REFERENCES "grafana_ml_model_cluster" ("id");

ALTER TABLE "grafana_ml_model_point_kmedoids" ADD FOREIGN KEY ("id_point") REFERENCES "grafana_ml_model_point" ("id");

ALTER TABLE "grafana_ml_model_centroid" ADD FOREIGN KEY ("index") REFERENCES "grafana_ml_model_index" ("id");

ALTER TABLE "grafana_ml_model_centroid" ADD FOREIGN KEY ("id_cluster") REFERENCES "grafana_ml_model_cluster" ("id");

ALTER TABLE "grafana_ml_model_centroid" ADD FOREIGN KEY ("id_feature") REFERENCES "grafana_ml_model_feature" ("id");



