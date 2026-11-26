# aws-finops-guard — AWS Cloud & LLM/Bedrock FinOps CLI + MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-15803d?style=for-the-badge)](./LICENSE)
[![MCP stdio](https://img.shields.io/badge/MCP-stdio%20Server-1c69d4?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Zero Dependencies](https://img.shields.io/badge/Python-3.10%2B%20Zero%20Deps-059669?style=for-the-badge)](#quick-start)
[![TuringTec Agent Studio](https://img.shields.io/badge/Live%20Demo-TuringTec%20Studio-4f46e5?style=for-the-badge)](https://gabhack.github.io/turingtec-agent-studio/)

Zero-dependency **Open-Core CLI & Model Context Protocol (MCP) Server** that audits AWS infrastructure snapshots and AI Agent / LLM token spend in seconds — locally, read-only, with **zero cloud credentials sent to any third party**.

> **Try the Live Browser Sandbox (Zero Install):**
> https://gabhack.github.io/turingtec-agent-studio/

---

## What It Detects Instantly (Free Read-Only Tier)

- **Unattached EBS Volumes (`FINOPS-EBS-001`)** & **Legacy `gp2` → `gp3` Savings (`FINOPS-EBS-002`)**
- **Idle NAT Gateways (`FINOPS-NET-001`)** & **Missing `$0` S3/DynamoDB VPC Gateway Endpoints (`FINOPS-NET-002`)**
- **Unassociated Elastic IPs (`FINOPS-NET-003`)**
- **Underutilized / Oversized Non-Prod RDS Instances (`FINOPS-RDS-001`)**
- **LLM / Bedrock / OpenAI / Gemini Token Waste (`FINOPS-LLM-001` & `FINOPS-LLM-002`):** catches classification/triage agents overpaying on premium models instead of fast-tier routing + prompt caching.

## Pro Tier (`$49` One-Time Individual / `$99` Team — Gumroad License Key)

- **`--remediate` / `generate_terraform_remediation` MCP tool:** outputs safe, copy-paste **Terraform HCL patches** + **AWS CLI commands** + Executive Markdown Report.
- **`--sarif`:** exports **SARIF 2.1.0** for GitHub Code Scanning & CI/CD FinOps gates.
- **14-day offline grace cache** + CI/CD env var (`AWS_FINOPS_GUARD_LICENSE_KEY`).
- 👉 **Get Pro License Key / Agent Kits:** https://gabbler407.gumroad.com/

---

## Quick Start

```bash
git clone https://github.com/gabhack/aws-finops-guard.git
cd aws-finops-guard
python3 -m aws_finops_guard.cli demo
```

### Connect as an MCP Server in Claude Desktop, Cursor, or VS Code (`mcp.json`)

```json
{
  "mcpServers": {
    "aws-finops-guard": {
      "command": "python3",
      "args": ["-m", "aws_finops_guard.cli", "mcp"],
      "cwd": "/path/to/aws-finops-guard"
    }
  }
}
```

### Activate Pro License Key

```bash
python3 -m aws_finops_guard.cli auth YOUR-GUMROAD-LICENSE-KEY
python3 -m aws_finops_guard.cli demo --remediate -o finops-report.md
```

---

## Built by TuringTec Agent Studio

- **Interactive Demos, B2B AI Agent Kits & ROI Calculator:** https://gabhack.github.io/turingtec-agent-studio/
- **Apify Dual-Mode MCP Server Suite:** https://github.com/gabhack/apify-cloud-mcp-suite
- **Multi-Cloud & AI Certification Simulator (CloudCert Lab):** https://gabhack.github.io/cloudcert-lab/
