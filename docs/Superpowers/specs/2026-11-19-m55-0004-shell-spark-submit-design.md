# M55-0004 in-container spark-submit PATH

`run_hydrate_raw_3m_incontainer.sh` and sibling wrappers call bare `spark-submit` under bash -lc. Use `/opt/spark/bin/spark-submit` (and spark-sql in hydrate_raw DAG DQ).
