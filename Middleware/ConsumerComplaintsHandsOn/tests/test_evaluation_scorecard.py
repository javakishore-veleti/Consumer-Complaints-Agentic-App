"""D93: golden-set EVALUATION harness for ladder configs."""

from pathlib import Path

from app.core.common.evaluation_scorecard import (
    SHIP_RECOMMENDATION,
    HitAtKReq,
    ReciprocalRankReq,
    RunScorecardReq,
    ScorecardAsDictsReq,
    hit_at_k,
    reciprocal_rank,
    run_scorecard,
    scorecard_as_dicts,
)

FIXTURE = Path(__file__).parent / "fixtures" / "intellect_golden_set.json"


def test_hit_at_k_and_mrr_helpers():
    assert hit_at_k(HitAtKReq(ranked_ids=["a", "b"], relevant_ids=["b"], k=1)) == 0.0
    assert hit_at_k(HitAtKReq(ranked_ids=["a", "b"], relevant_ids=["b"], k=2)) == 1.0
    assert reciprocal_rank(ReciprocalRankReq(ranked_ids=["x", "b"], relevant_ids=["b"])) == 0.5


def test_golden_scorecard_runs_all_ladder_configs():
    assert FIXTURE.is_file()
    rows = run_scorecard(RunScorecardReq(golden_path=FIXTURE))
    names = [r.config for r in rows]
    assert names == [
        "baseline",
        "hybrid",
        "self_query",
        "decompose",
        "reranker",
        "everything",
        "signatures",
    ]
    assert all(r.queries == 5 for r in rows)
    by = {r.config: r for r in rows}
    assert by["hybrid"].hit_at_5 >= 0.8
    assert by["reranker"].hit_at_5 >= 0.8
    assert SHIP_RECOMMENDATION == "reranker"
    as_dicts = scorecard_as_dicts(ScorecardAsDictsReq(rows=rows))
    assert as_dicts[0]["config"] == "baseline"
