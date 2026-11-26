#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI entry point for aws-finops-guard (Open-Core + Gumroad Pro License)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .auditor import SAMPLE_SNAPSHOT, audit_snapshot, render_markdown_report, render_sarif
from .licensing import GUMROAD_CHECKOUT_URL, has_active_pro_license, save_license_cache, verify_license_remote
from .mcp_server import serve_stdio


def cmd_audit(args: argparse.Namespace) -> int:
    if args.file:
        snap = json.loads(Path(args.file).read_text(encoding="utf-8"))
    else:
        snap = SAMPLE_SNAPSHOT

    res = audit_snapshot(snap)
    wants_pro = bool(args.remediate or args.sarif)
    pro_ok = False
    pro_note = ""
    if wants_pro:
        pro_ok, pro_note = has_active_pro_license()
        if not pro_ok:
            print(f"\n[PRO REQUIRED] Detected ${res['estimated_monthly_savings_usd']:,.2f}/mo (${res['estimated_annual_savings_usd']:,.2f}/yr) in avoidable cloud/LLM spend.")
            print(f"  -> {pro_note}")
            print("  -> Activate with: aws-finops-guard auth <GUMROAD_LICENSE_KEY>\n")
            return 2

    if args.sarif:
        out = json.dumps(render_sarif(res), indent=2)
    elif args.json:
        out = json.dumps(res, indent=2)
    else:
        out = render_markdown_report(res, include_remediation=bool(args.remediate and pro_ok))

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"Saved report -> {args.output}")
    else:
        print(out)

    if not wants_pro:
        print(
            f"[TIP] Unlock Terraform HCL auto-remediation & CI/CD SARIF export for $49 one-time -> {GUMROAD_CHECKOUT_URL}",
            file=sys.stderr,
        )
    return 0


def cmd_auth(args: argparse.Namespace) -> int:
    try:
        res = verify_license_remote(args.license_key, increment_uses=True)
    except Exception as exc:
        print(f"ERROR contacting Gumroad License API: {exc}", file=sys.stderr)
        return 1
    if not res["valid"]:
        print("INVALID LICENSE KEY. Purchase a Pro license at:", GUMROAD_CHECKOUT_URL, file=sys.stderr)
        return 1
    save_license_cache(args.license_key, res.get("email", ""))
    print(f"OK: Pro license activated for {res.get('email') or 'user'} (14-day offline grace enabled).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aws-finops-guard",
        description="AWS Cloud & LLM/Bedrock FinOps Guardrails CLI + MCP Server (Open-Core)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_demo = sub.add_parser("demo", help="Run read-only FinOps audit on built-in AWS + LLM sample snapshot")
    p_demo.add_argument("--json", action="store_true", help="Output JSON")
    p_demo.add_argument("--remediate", action="store_true", help="[PRO] Include Terraform HCL & AWS CLI patches")
    p_demo.add_argument("--sarif", action="store_true", help="[PRO] Output CI/CD SARIF 2.1.0 JSON")
    p_demo.add_argument("-o", "--output", help="Write report to file")
    p_demo.set_defaults(file=None, func=cmd_audit)

    p_audit = sub.add_parser("audit", help="Run read-only FinOps audit on a local JSON snapshot")
    p_audit.add_argument("file", help="Path to AWS/LLM snapshot JSON file")
    p_audit.add_argument("--json", action="store_true", help="Output JSON")
    p_audit.add_argument("--remediate", action="store_true", help="[PRO] Include Terraform HCL & AWS CLI patches")
    p_audit.add_argument("--sarif", action="store_true", help="[PRO] Output CI/CD SARIF 2.1.0 JSON")
    p_audit.add_argument("-o", "--output", help="Write report to file")
    p_audit.set_defaults(func=cmd_audit)

    p_auth = sub.add_parser("auth", help="Activate Gumroad Pro License Key")
    p_auth.add_argument("license_key", help="Gumroad Pro license key")
    p_auth.set_defaults(func=cmd_auth)

    p_mcp = sub.add_parser("mcp", help="Run JSON-RPC 2.0 stdio MCP Server for Claude Desktop / Cursor / VS Code")
    p_mcp.set_defaults(func=lambda _a: (serve_stdio() or 0))

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
