import argparse
import json

from app.diagnostics import run_diagnosis
from app.history import init_db, list_reports, save_report
from app.proxies import load_proxies


def cmd_diagnose(args: argparse.Namespace) -> None:
    init_db()
    try:
        report = run_diagnosis(args.url, proxy_label=args.proxy, follow_redirects=not args.no_redirects)
    except ValueError as exc:
        print(f"error: {exc}")
        return

    save_report(report)

    if args.json:
        print(report.model_dump_json(indent=2))
        return

    print(f"correlation_id: {report.correlation_id}")
    print(f"target:         {report.target_url}")
    print(f"dns:            {report.dns.resolved_ips or 'FAILED: ' + str(report.dns.error)} ({report.dns.resolution_time_ms:.1f} ms)")
    print(f"direct:         {report.direct.status_code} [{report.direct.classification}] {report.direct.latency_ms:.1f} ms")
    if report.proxy:
        print(f"proxy ({report.proxy.proxy_label}): {report.proxy.status_code} [{report.proxy.classification}] {report.proxy.latency_ms:.1f} ms")


def cmd_list_proxies(_: argparse.Namespace) -> None:
    proxies = load_proxies()
    if not proxies:
        print("No proxies configured. Copy proxies.example.yaml to proxies.yaml and fill in your own.")
        return
    for p in proxies:
        print(f"{p.label:15} {p.region:12} {p.url}")


def cmd_history(args: argparse.Namespace) -> None:
    init_db()
    for row in list_reports(limit=args.limit):
        print(json.dumps(row))


def main() -> None:
    parser = argparse.ArgumentParser(description="Web access diagnostics CLI")
    subparsers = parser.add_subparsers(required=True)

    diagnose_parser = subparsers.add_parser("diagnose", help="Run a diagnosis against a URL")
    diagnose_parser.add_argument("url")
    diagnose_parser.add_argument("--proxy", help="Proxy label from proxies.yaml to compare against direct")
    diagnose_parser.add_argument("--no-redirects", action="store_true", help="Don't follow redirects")
    diagnose_parser.add_argument("--json", action="store_true", help="Print full JSON report")
    diagnose_parser.set_defaults(func=cmd_diagnose)

    list_parser = subparsers.add_parser("list-proxies", help="List configured proxies")
    list_parser.set_defaults(func=cmd_list_proxies)

    history_parser = subparsers.add_parser("history", help="Show recent diagnosis runs")
    history_parser.add_argument("--limit", type=int, default=20)
    history_parser.set_defaults(func=cmd_history)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
