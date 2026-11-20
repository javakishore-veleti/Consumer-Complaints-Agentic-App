"""Category → workflow_name filters for Admin Workflow Logs (M55-0012 / #394)."""

from __future__ import annotations

from dataclasses import dataclass

WORKFLOW_LOG_PAGE_SIZE_MAX = 30

WORKFLOW_LOG_CATEGORIES = frozenset(
    {"import", "db_ingest", "raw", "refined", "curated", "taxonomy", "chroma"}
)


@dataclass(frozen=True)
class WorkflowLogCategoryFilter:
    """OR of startswith prefixes; optional exclude startswith (db_ingest vs imports)."""

    prefixes: tuple[str, ...]
    exclude_prefix: str | None = None


CATEGORY_FILTERS: dict[str, WorkflowLogCategoryFilter] = {
    "import": WorkflowLogCategoryFilter(
        prefixes=("download_cfpb", "filter_cfpb", "ingest_cfpb_imports"),
    ),
    "db_ingest": WorkflowLogCategoryFilter(
        prefixes=("ingest_cfpb",),
        exclude_prefix="ingest_cfpb_imports",
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
