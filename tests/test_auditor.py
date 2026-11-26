#!/usr/bin/env python3
"""Unit tests for aws-finops-guard auditor & MCP server."""

import json
import unittest

from aws_finops_guard.auditor import SAMPLE_SNAPSHOT, audit_snapshot, render_markdown_report, render_sarif
from aws_finops_guard.mcp_server import handle_rpc


class TestAwsFinopsGuard(unittest.TestCase):
    def test_sample_snapshot_detects_all_waste_categories(self):
        res = audit_snapshot(SAMPLE_SNAPSHOT)
        self.assertGreaterEqual(res["findings_count"], 6)
        self.assertGreater(res["estimated_monthly_savings_usd"], 400.0)
        rule_ids = {f["rule_id"] for f in res["findings"]}
        self.assertIn("FINOPS-EBS-001", rule_ids)
        self.assertIn("FINOPS-EBS-002", rule_ids)
        self.assertIn("FINOPS-NET-001", rule_ids)
        self.assertIn("FINOPS-NET-002", rule_ids)
        self.assertIn("FINOPS-RDS-001", rule_ids)
        self.assertIn("FINOPS-LLM-001", rule_ids)

    def test_markdown_and_sarif_generation(self):
        res = audit_snapshot(SAMPLE_SNAPSHOT)
        md = render_markdown_report(res, include_remediation=True)
        self.assertIn("aws_vpc_endpoint", md)
        sarif = render_sarif(res)
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(len(sarif["runs"][0]["results"]), res["findings_count"])

    def test_mcp_rpc_tools_list_and_audit(self):
        r_list = handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(len(r_list["result"]["tools"]), 3)
        r_call = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "audit_aws_finops_snapshot", "arguments": {}},
            }
        )
        data = json.loads(r_call["result"]["content"][0]["text"])
        self.assertGreater(data["estimated_monthly_savings_usd"], 400.0)


if __name__ == "__main__":
    unittest.main()
