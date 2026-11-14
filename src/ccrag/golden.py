"""The golden set: questions with exact ground truth, built from the data itself.

No LLM is involved, so the set is free, reproducible, and the answers cannot be wrong.

Complaint questions describe a complaint with just enough fields that exactly one indexed complaint matches
(or, for `filtered`, a set of them), so the evidence is the chunk id(s) and the reference answer is read straight
from the record. Doc and refusal questions are hand-written in `corpus/golden_manual.csv`; a doc question names an
evidence phrase and we find the chunks that contain it.

Types:
  lookup    several fields identify one complaint; ask how the company responded, etc.
  keyword   only the complaint ID identifies it (BM25's job; embeddings can't tell two numbers apart)
  filtered  "an example complaint about X from state Y in year Z": many chunks qualify (self-query's job)
  two_part  two lookup/keyword questions joined together (decomposition's job)
  docs      what a field means, from the field reference
  refusal   not answerable from the corpus: the bot must refuse

`evidence` is pieces joined with `||`; a piece is chunk ids joined with `|`; a piece counts as found when any of
its chunk ids is retrieved. A two-part question has two pieces.
"""
import random
from collections import defaultdict
from itertools import zip_longest

import pandas as pd

from .chunking import Chunk, build_chunks, month_name
from .config import GOLDEN_PATH, MANUAL_GOLDEN
from .ingest import load_complaints

PIECE, ALT = "||", "|"
ATTRS = ["company", "product", "issue", "sub_issue", "state", "month", "submitted_via", "tags"]


def attr_value(r: dict, attr: str):
    return r["date_received"][:7] if attr == "month" else r[attr]


def phrase(r: dict, attr: str) -> str:
    return {
        "company": f"against {r['company']}",
        "product": f"about {r['product']}" + (f" ({r['sub_product']})" if r["sub_product"] else ""),
        "issue": f"with the issue \"{r['issue']}\"",
        "sub_issue": f"and sub-issue \"{r['sub_issue']}\"",
        "state": f"from a consumer in {r['state']}",
        "month": f"received in {month_name(r['date_received'])}",
        "submitted_via": f"submitted via {r['submitted_via']}",
        "tags": f"tagged \"{r['tags']}\"",
    }[attr]


def matching(records: list[dict], r: dict, attrs: list[str]) -> list[dict]:
    return [o for o in records if all(attr_value(o, a) == attr_value(r, a) for a in attrs)]


def identify(r: dict, records: list[dict], rng: random.Random, exclude=(), max_attrs=4) -> list[str] | None:
    """Add attributes in random order until exactly one record matches. None if it takes too many."""
    pool = [a for a in ATTRS if a not in exclude and attr_value(r, a) is not None]
    rng.shuffle(pool)
    chosen = []
    for a in pool[:max_attrs]:
        chosen.append(a)
        if len(matching(records, r, chosen)) == 1:
            return [a for a in ATTRS if a in chosen]  # keep a natural reading order
    return None


def yes_no(value):
    return {True: "yes", False: "no"}.get(value)


ASKS = {
    "response": ("How did the company respond to the consumer, and was the response timely?", set(),
                 lambda r: f"The company's response was \"{r['company_response']}\"."
                           + (f" Timely response: {yes_no(r['timely'])}." if r["timely"] is not None else "")),
    "public": ("What was the company's public response?", set(),
               lambda r: f"The company's public response was \"{r['company_public_response']}\"."),
    "channel": ("How was it submitted to the CFPB, and when was it sent to the company?", {"submitted_via"},
                lambda r: f"It was submitted via {r['submitted_via']} and sent to the company on {r['date_sent_to_company']}."),
}


def can_ask(r: dict, ask: str) -> bool:
    return {"response": r["company_response"] is not None,
            "public": r["company_public_response"] is not None,
            "channel": r["date_sent_to_company"] is not None}[ask]


def chunk_id(r: dict) -> str:
    return f"cfpb-{r['complaint_id']}"


def interleave_by_product(records: list[dict], rng: random.Random) -> list[dict]:
    groups = defaultdict(list)
    for r in records:
        groups[r["product"]].append(r)
    for g in groups.values():
        rng.shuffle(g)
    order = list(groups.values())
    rng.shuffle(order)
    return [r for row in zip_longest(*order) for r in row if r is not None]


def lookup_questions(records, rng, n) -> list[dict]:
    out, asks = [], list(ASKS)
    for r in interleave_by_product(records, rng):
        if len(out) == n:
            break
        ask = asks[len(out) % len(asks)]
        text, exclude, answer = ASKS[ask]
        if not can_ask(r, ask):
            continue
        attrs = identify(r, records, rng, exclude=exclude)
        if attrs is None:
            continue
        question = "Find the CFPB complaint " + ", ".join(phrase(r, a) for a in attrs) + f". {text}"
        out.append({"type": "lookup", "question": question, "evidence": chunk_id(r), "reference_answer": answer(r)})
    return out


KEYWORD_ASKS = [
    ("What was the company's response to CFPB complaint {id}, and was it timely?", ASKS["response"][2], "response"),
    ("What product and issue does CFPB complaint {id} concern?",
     lambda r: f"Product: {r['product']}. Issue: {r['issue']}.", None),
    ("Which company is CFPB complaint {id} about, and in which state is the consumer?",
     lambda r: f"The complaint is about {r['company']} and the consumer is in {r['state']}.", None),
]


def keyword_questions(records, rng, n) -> list[dict]:
    out = []
    for r in interleave_by_product(records, rng):
        if len(out) == n:
            break
        text, answer, needs = KEYWORD_ASKS[len(out) % len(KEYWORD_ASKS)]
        if needs and not can_ask(r, needs):
            continue
        out.append({"type": "keyword", "question": text.format(id=r["complaint_id"]), "evidence": chunk_id(r),
                    "reference_answer": answer(r)})
    return out


def filtered_questions(records, rng, n) -> list[dict]:
    """Sets of 3 to 40 complaints that share (product, state, year) or (company, year, company_response)."""
    by_a, by_b = defaultdict(list), defaultdict(list)
    for r in records:
        year = r["date_received"][:4]
        by_a[(r["product"], r["state"], year)].append(r)
        by_b[(r["company"], year, r["company_response"])].append(r)
    cells = [("a", k, v) for k, v in by_a.items() if 3 <= len(v) <= 40] + \
            [("b", k, v) for k, v in by_b.items() if 3 <= len(v) <= 40 and k[2]]
    cells.sort(key=lambda c: (c[0], str(c[1])))
    rng.shuffle(cells)
    out = []
    for kind, key, rs in cells[:n]:
        if kind == "a":
            product, state, year = key
            question = f"Give me an example complaint about {product} from a consumer in {state} received in {year}."
            criteria = f"product {product}, state {state}, received in {year}"
        else:
            company, year, response = key
            question = (f"Give me an example complaint against {company} received in {year} "
                        f"where the company's response was \"{response}\".")
            criteria = f"company {company}, received in {year}, company response \"{response}\""
        ids = ", ".join(r["complaint_id"] for r in sorted(rs, key=lambda r: r["complaint_id"])[:8])
        out.append({"type": "filtered", "question": question,
                    "evidence": ALT.join(chunk_id(r) for r in rs),
                    "reference_answer": f"Any complaint matching ({criteria}). Matching complaint IDs include: {ids}."})
    return out


def two_part_questions(singles: list[dict], rng, n) -> list[dict]:
    """Join pairs of single-complaint questions about different complaints."""
    pool = singles[:]
    rng.shuffle(pool)
    out = []
    for a, b in zip(pool[0::2], pool[1::2]):
        if len(out) == n:
            break
        out.append({"type": "two_part", "question": f"{a['question']} Also: {b['question'][0].lower()}{b['question'][1:]}",
                    "evidence": PIECE.join([a["evidence"], b["evidence"]]),
                    "reference_answer": f"(1) {a['reference_answer']} (2) {b['reference_answer']}"})
    return out


def norm(text: str) -> str:
    return " ".join(text.lower().split())


def manual_questions(chunks: list[Chunk]) -> list[dict]:
    rows, docs = pd.read_csv(MANUAL_GOLDEN, keep_default_na=False), [c for c in chunks if c.meta["kind"] == "doc"]
    out = []
    for row in rows.itertuples():
        evidence = ""
        if row.evidence_phrase:
            ids = [c.id for c in docs if norm(row.evidence_phrase) in norm(c.text)]
            if not ids:
                raise ValueError(f"{row.id}: evidence phrase not found in any chunk: {row.evidence_phrase!r}")
            evidence = ALT.join(ids)
        out.append({"id": row.id, "type": row.type, "question": row.question, "evidence": evidence,
                    "reference_answer": row.reference_answer, "should_refuse": str(row.should_refuse) == "True"})
    return out


def build_golden(seed: int = 11, lookup=12, keyword=6, filtered=8, two_part=8) -> pd.DataFrame:
    rng = random.Random(seed)
    records, chunks = load_complaints(), build_chunks()
    singles = lookup_questions(records, rng, lookup + two_part) + keyword_questions(records, rng, keyword + 4)
    rows = singles[:lookup] + singles[lookup + two_part:lookup + two_part + keyword]
    rows = [r for r in singles if r["type"] == "lookup"][:lookup] + [r for r in singles if r["type"] == "keyword"][:keyword]
    spare = [r for r in singles if r not in rows]
    rows += filtered_questions(records, rng, filtered) + two_part_questions(spare, rng, two_part)
    prefix = {"lookup": "l", "keyword": "k", "filtered": "f", "two_part": "t"}
    counts = defaultdict(int)
    for r in rows:
        counts[r["type"]] += 1
        r["id"], r["should_refuse"] = f"{prefix[r['type']]}{counts[r['type']]:02d}", False
    rows += manual_questions(chunks)
    df = pd.DataFrame(rows, columns=["id", "type", "question", "evidence", "reference_answer", "should_refuse"])
    GOLDEN_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(GOLDEN_PATH, index=False)
    return df


def load_golden() -> pd.DataFrame:
    if not GOLDEN_PATH.exists():
        raise FileNotFoundError(f"{GOLDEN_PATH} not found. Run: ccrag golden")
    df = pd.read_csv(GOLDEN_PATH, keep_default_na=False)
    df["should_refuse"] = df["should_refuse"].astype(str) == "True"
    return df


def pieces(row) -> list[set[str]]:
    return [set(p.split(ALT)) for p in row.evidence.split(PIECE)] if row.evidence else []
