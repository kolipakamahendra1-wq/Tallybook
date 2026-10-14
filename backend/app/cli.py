"""Usage: python -m app.cli AAPL [--offline] [--llm] [--json]"""
import argparse
import json
import sys

from .data import DataError
from .graph import research
from .llm import LLMError, get_client


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="stock-research")
    p.add_argument("ticker")
    p.add_argument("--offline", action="store_true", help="use bundled synthetic fixtures (no network)")
    p.add_argument("--llm", action="store_true", help="write the brief with the configured LLM provider")
    p.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = p.parse_args(argv)

    try:
        llm = get_client() if args.llm else None
        report = research(args.ticker, offline=args.offline, llm=llm)
    except (DataError, LLMError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print(f"{report['ticker']}  {report['rating']}  score {report['score']:+.2f}  risk {report['risk_label']}  ({report['mode']}, {report['elapsed_ms']} ms)")
    for a in report["agents"]:
        print(f"  [{a['status']:8}] {a['agent']:13} {a['score']:+.2f}  {a['summary'] if a['status'] == 'ok' else a['error']}")
    print("\n" + report["brief"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
