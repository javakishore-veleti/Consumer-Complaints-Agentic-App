# M52-0003 signatures config

`POST /intellect/query` config=`signatures` searches `cfpb_semantic_signatures` via local JSONL mirror under `CCA_VECTOR_STORE_PATH`, else live Chroma (`CCA_CHROMA_URL`). Empty/missing → empty hits (200).
