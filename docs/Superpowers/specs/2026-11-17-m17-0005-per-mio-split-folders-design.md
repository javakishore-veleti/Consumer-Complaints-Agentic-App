# M17-0005 — Per-MIO split source folders

Each Imports MIO uses its own env var / default under `$HOME/Downloads/temp/`:
`complaints_split_{3_months,6_months,9_months,12_months,all}_data`.
Filter (3m) → `CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS`; All download/stage → `CCA_CFPB_SPLIT_SOURCE_PATH_ALL`.
