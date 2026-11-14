"""Turn complaints and docs into chunks.

A complaint is ~10 short fields, so the chunk *is* the complaint: one record, one chunk, written out as
sentences so that both the embedder and BM25 see the product, issue, company, state and dates as words.
The field-reference page is real prose, so it goes through the same 500/100 token splitter as the video.

Every chunk carries the same metadata keys (None where they don't apply), because the metadata columns are
what the self-query step filters on.
"""
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from pathlib import Path

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import DOCS_DIR
from .ingest import load_complaints

FILTER_COLUMNS = ["kind", "product", "company", "state", "year", "company_response", "timely",
                  "submitted_via", "older_american", "servicemember"]


@dataclass
class Chunk:
    id: str
    text: str
    meta: dict = field(default_factory=dict)

    @property
    def page_content(self) -> str:  # same name the notebook's LangChain Documents used
        return self.text


@cache
def tokenizer():
    return tiktoken.get_encoding("cl100k_base")


def month_name(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%B %Y")


def complaint_text(r: dict) -> str:
    product = r["product"] + (f" / {r['sub_product']}" if r["sub_product"] else "")
    issue = r["issue"] + (f" / {r['sub_issue']}" if r["sub_issue"] else "")
    parts = [
        f"CFPB complaint {r['complaint_id']}, received {r['date_received']} ({month_name(r['date_received'])}), "
        f"submitted via {r['submitted_via']}.",
        f"Product: {product}.",
        f"Issue: {issue}.",
        f"Company: {r['company']}.",
        f"Consumer location: state {r['state']}" + (f", ZIP {r['zip_code']}." if r["zip_code"] else "."),
    ]
    if r["tags"]:
        parts.append(f"Tags: {r['tags']}.")
    if r["date_sent_to_company"]:
        parts.append(f"Sent to the company on {r['date_sent_to_company']}.")
    parts.append(f"Company response to consumer: {r['company_response']}.")
    if r["company_public_response"]:
        parts.append(f"Company public response: {r['company_public_response']}.")
    if r["timely"] is not None:
        parts.append(f"Timely response: {'yes' if r['timely'] else 'no'}.")
    return " ".join(parts)


def complaint_meta(r: dict) -> dict:
    tags = r["tags"] or ""
    return {
        "kind": "complaint", "doc_id": r["complaint_id"], "complaint_id": r["complaint_id"],
        "date_received": r["date_received"], "year": int(r["date_received"][:4]),
        "product": r["product"], "sub_product": r["sub_product"], "issue": r["issue"], "sub_issue": r["sub_issue"],
        "company": r["company"], "state": r["state"], "company_response": r["company_response"],
        "submitted_via": r["submitted_via"], "timely": r["timely"],
        "older_american": "Older American" in tags, "servicemember": "Servicemember" in tags,
    }


def complaint_chunks(records: list[dict]) -> list[Chunk]:
    chunks = []
    for r in records:
        text = complaint_text(r)
        meta = complaint_meta(r) | {"chunk_index": 0, "n_tokens": len(tokenizer().encode(text))}
        chunks.append(Chunk(f"cfpb-{r['complaint_id']}", text, meta))
    return chunks


def doc_chunks(docs_dir: Path = DOCS_DIR) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base", separators=["\n\n", ". ", "\n", " ", ""], chunk_size=500, chunk_overlap=100,
        keep_separator="end")
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        for i, text in enumerate(splitter.split_text(path.read_text(encoding="utf-8"))):
            meta = {"kind": "doc", "doc_id": path.stem, "chunk_index": i, "n_tokens": len(tokenizer().encode(text))}
            chunks.append(Chunk(f"{path.stem}-c{i}", text, meta))
    return chunks


def build_chunks() -> list[Chunk]:
    return [*complaint_chunks(load_complaints()), *doc_chunks()]
