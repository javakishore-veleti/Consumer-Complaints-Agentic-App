# M55-0005 hydrate_raw missing table

Fresh Iceberg has no `demo.raw.cfpb_complaints_3m`. Use `CREATE NAMESPACE IF NOT EXISTS` + `writeTo(...).createOrReplace()` instead of `DELETE FROM`.
