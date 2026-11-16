# M06 #172/#173/#174 Split CFPB landing + SoT ingest — plan

**Goal:** D91 split parts under `LOCAL_DATA_PATH_CFPB`, stage from `CCA_CFPB_SPLIT_SOURCE_PATH`, ingest all parts into Mongo.

1. Spec D91.
2. `ccaa/split_parts.py` + unit tests.
3. Update `download_cfpb_all` / `ingest_cfpb_all` + `ingest_complaints_parts`.
4. Alembic `0017` + Mongo bootstrap + upsert list / `.env.example`.
5. Schema/DAG smoke tests; DESIGN + PRODUCT_FEATURES.
6. PR → merge → close stories/features/epic.
