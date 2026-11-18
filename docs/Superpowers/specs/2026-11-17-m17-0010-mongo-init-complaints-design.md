# M17-0010 — Mongo first-boot init for complaints

Mount `docker-entrypoint-initdb.d/01-init-complaints.js` so an empty volume creates `consumer_comp_db.complaints` with unique `Complaint ID` (D86). Document Compass auth URL. Interval-isolation collections are out of scope (later story).
