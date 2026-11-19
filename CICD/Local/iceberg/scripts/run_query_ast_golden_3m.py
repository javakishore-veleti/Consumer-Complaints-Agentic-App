"""Execute Golden Query AST cases against SparkSQL curated table (M50-0001 / #338)."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from query_ast import AstToSqlReq, KAnonReq, assert_k_anonymous, ast_to_sql  # noqa: E402


def _parse_count(spark_out: str) -> int:
    nums = re.findall(r"(?m)^(\d+)\s*$", spark_out)
    if not nums:
        # spark-sql sometimes prints "Time taken" after; take last standalone int line
        for line in reversed(spark_out.splitlines()):
            line = line.strip()
            if line.isdigit():
                return int(line)
        raise ValueError(f"could not parse COUNT from spark output:\n{spark_out[-500:]}")
    return int(nums[-1])


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--golden",
        default=str(SCRIPTS.parent / "golden" / "query_ast_golden_3m.json"),
    )
    p.add_argument(
        "--container",
        default=os.environ.get("CCA_ICEBERG_SPARK_CONTAINER", "cca-spark-iceberg"),
    )
    p.add_argument("--strict-exact", action="store_true", default=True)
    args = p.parse_args()

    suite = json.loads(Path(args.golden).read_text(encoding="utf-8"))
    cases = suite.get("cases") or []
    if not cases:
        print("FAIL: no golden cases", file=sys.stderr)
        return 1

    passed = 0
    for case in cases:
        cid = case.get("id")
        sql = ast_to_sql(AstToSqlReq(case["ast"]))
        print(f"CASE {cid}")
        print(f"SQL {sql}")
        out = subprocess.check_output(
            ["docker", "exec", args.container, "spark-sql", "-e", sql],
            text=True,
            stderr=subprocess.STDOUT,
        )
        n = _parse_count(out)
        expect = case.get("expect") or {}
        min_count = int(expect.get("min_count") or 10)
        exact = expect.get("exact_count")
        assert_k_anonymous(KAnonReq(n))
        if n < min_count:
            print(f"FAIL {cid}: n={n} < min_count={min_count}", file=sys.stderr)
            return 1
        if exact is not None and int(exact) != n:
            print(f"FAIL {cid}: n={n} != exact_count={exact}", file=sys.stderr)
            return 1
        print(f"PASS {cid}: n={n}")
        passed += 1

    print(f"PASS: golden suite {suite.get('suite')} cases={passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
