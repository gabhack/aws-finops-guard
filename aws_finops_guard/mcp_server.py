#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zero-Dependency JSON-RPC 2.0 stdio MCP Server for AWS & AI FinOps Guardrails.
Works directly inside Claude Desktop, Cursor, VS Code, Windsurf, and Antigravity.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from .auditor import LLM_PRICING_PER_1M, SAMPLE_SNAPSHOT, audit_snapshot, render_markdown_report
from .licensing import GUMROAD_CHECKOUT_URL, has_active_pro_license

TOOLS = [
    {
        "name": "audit_aws_finops_snapshot",
        "description": "Free Read-Only FinOps audit of an AWS + LLM workload JSON snapshot. Detects idle EBS/gp2, NAT Gateways without S3 Gateway Endpoints, unattached EIPs, oversized RDS, and LLM token waste.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "snapshot": {
                    "type": "object",
                    "description": "AWS resource & LLM workload JSON snapshot (omit to run on built-in sample).",
                }
            },
        },
    },
    {
        "name": "compare_llm_token_cost",
        "description": "Free calculator comparing monthly USD spend across Claude, GPT-4o, Gemini 2.5, and Amazon Nova models for given input/output millions of tokens.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "monthly_input_millions": {"type": "number", "minimum": 0},
                "monthly_output_millions": {"type": "number", "minimum": 0},
            },
            "required": ["monthly_input_millions", "monthly_output_millions"],
        },
    },
    {
        "name": "generate_terraform_remediation",
        "description": "[PRO LICENSE] Generates copy-paste safe Terraform HCL patches, AWS CLI commands, and Markdown Executive Report for a FinOps snapshot.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "snapshot": {"type": "object", "description": "AWS resource & LLM workload JSON snapshot."}
            },
        },
    },
]


def handle_rpc(msg: dict[str, Any]) -> dict[str, Any] | None:
    req_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params") or {}

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "aws-finops-guard-mcp", "version": "0.1.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        if name == "audit_aws_finops_snapshot":
            snap = args.get("snapshot") or SAMPLE_SNAPSHOT
            result = audit_snapshot(snap)
            compact = {
                "account_alias": result["account_alias"],
                "region": result["region"],
                "findings_count": result["findings_count"],
                "estimated_monthly_savings_usd": result["estimated_monthly_savings_usd"],
                "estimated_annual_savings_usd": result["estimated_annual_savings_usd"],
                "findings": [
                    {
                        "rule_id": f["rule_id"],
                        "severity": f["severity"],
                        "resource": f["resource"],
                        "monthly_waste_usd": f["monthly_waste_usd"],
                        "summary": f["summary"],
                        "recommendation": f["recommendation"],
                    }
                    for f in result["findings"]
                ],
                "pro_remediation_url": GUMROAD_CHECKOUT_URL,
            }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(compact, indent=2)}]},
            }
        if name == "compare_llm_token_cost":
            in_m = float(args.get("monthly_input_millions", 0) or 0)
            out_m = float(args.get("monthly_output_millions", 0) or 0)
            rows = sorted(
                [
                    {
                        "model": m,
                        "tier": p["tier"],
                        "monthly_usd": round(in_m * p["input"] + out_m * p["output"], 2),
                    }
                    for m, p in LLM_PRICING_PER_1M.items()
                ],
                key=lambda x: x["monthly_usd"],
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps({"models": rows}, indent=2)}]},
            }
        if name == "generate_terraform_remediation":
            snap = args.get("snapshot") or SAMPLE_SNAPSHOT
            result = audit_snapshot(snap)
            ok, note = has_active_pro_license()
            if not ok:
                payload = {
                    "pro_locked": True,
                    "estimated_monthly_savings_usd": result["estimated_monthly_savings_usd"],
                    "estimated_annual_savings_usd": result["estimated_annual_savings_usd"],
                    "message": f"Detected ${result['estimated_monthly_savings_usd']:,.2f}/mo in waste. {note}",
                    "checkout_url": GUMROAD_CHECKOUT_URL,
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"isError": False, "content": [{"type": "text", "text": json.dumps(payload, indent=2)}]},
                }
            md = render_markdown_report(result, include_remediation=True)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": md}]},
            }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]},
        }
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def serve_stdio() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            resp = handle_rpc(msg)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()
