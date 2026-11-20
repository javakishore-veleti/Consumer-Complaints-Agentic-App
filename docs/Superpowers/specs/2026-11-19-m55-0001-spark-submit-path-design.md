# M55-0001 spark-submit PATH

`bash -lc` inside `cca-spark-iceberg` drops `/opt/spark/bin`. Use absolute `/opt/spark/bin/spark-submit` and `spark-sql` in `lakehouse_spark.py`.
