// M17-0010 / #259 — first-boot only (empty data volume).
// Complaint document store: consumer_comp_db.complaints (D86).
// Interval isolation (3m vs 6m) is a later story; do not merge across MIOs then.

const dbName = "consumer_comp_db";
const collName = "complaints";

const appDb = db.getSiblingDB(dbName);
appDb.createCollection(collName);
appDb[collName].createIndex(
  { "Complaint ID": 1 },
  { unique: true, name: "uniq_complaint_id" }
);

print(`initialized ${dbName}.${collName} with uniq_complaint_id`);
