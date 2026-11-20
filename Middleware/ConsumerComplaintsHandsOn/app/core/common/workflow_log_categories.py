"""Category → workflow_name filters for Admin Workflow Logs (M55-0012 / #394)."""

from __future__ import annotations

from dataclasses import dataclass

WORKFLOW_LOG_PAGE_SIZE_MAX = 60

# Human labels for EngineType codes (unknown codes fall back to the raw value in the API/UI).
ENGINE_TYPE_LABELS = {
    "apache_airflow": "Apache Airflow",
    "aws_step_functions": "AWS Step Functions",
    "spring_batch": "Spring Batch",
    "bpmn": "BPMN",
    "spark_job": "Spark job",
    "aws_emr": "AWS EMR",
}

WORKFLOW_LOG_CATEGORIES = frozenset(
    {"import", "db_ingest", "raw", "refined", "curated", "taxonomy", "chroma"}
)


@dataclass(frozen=True)
class WorkflowLogCategoryFilter:
    """OR of startswith prefixes; optional exclude startswith (db_ingest vs imports)."""

    prefixes: tuple[str, ...]
    exclude_prefix: str | None = None


CATEGORY_FILTERS: dict[str, WorkflowLogCategoryFilter] = {
    # DataSets Import page: land/filter only (not DB ingest wrappers).
    "import": WorkflowLogCategoryFilter(
        prefixes=("download_cfpb", "filter_cfpb"),
    ),
    # DB Ingest page starts ingest_cfpb_imports_wrapper (and ingest_cfpb_all).
    "db_ingest": WorkflowLogCategoryFilter(
        prefixes=("ingest_cfpb",),
    ),
    "raw": WorkflowLogCategoryFilter(prefixes=("hydrate_raw",)),
    "refined": WorkflowLogCategoryFilter(prefixes=("hydrate_refined",)),
    "curated": WorkflowLogCategoryFilter(prefixes=("hydrate_curated",)),
    "taxonomy": WorkflowLogCategoryFilter(prefixes=("hydrate_taxonomy",)),
    "chroma": WorkflowLogCategoryFilter(prefixes=("hydrate_chroma", "index_cfpb_chroma")),
}


# Map D30 exec statuses → Workflow Logs UI vocabulary (inline dict; no bare-arg helpers — D37 / ctx-only).
DISPLAY_STATUS = {
    "requested": "started",
    "started": "started",
    "completed": "completed",
    "failed": "failed",
}
