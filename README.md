# aws-finops-guard — AWS Cloud & LLM/Bedrock FinOps CLI + MCP Server

[![CI](https://github.com/gabhack/aws-finops-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/gabhack/aws-finops-guard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-15803d?style=for-the-badge)](./LICENSE)
[![MCP stdio](https://img.shields.io/badge/MCP-stdio%20Server-1c69d4?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Zero Dependencies](https://img.shields.io/badge/Python-3.10%2B%20Zero%20Deps-059669?style=for-the-badge)](#quick-start)
[![TuringTec Agent Studio](https://img.shields.io/badge/Live%20Demo-TuringTec%20Studio-4f46e5?style=for-the-badge)](https://gabhack.github.io/turingtec-agent-studio/)

Zero-dependency **Open-Core CLI & Model Context Protocol (MCP) Server** that audits AWS infrastructure snapshots and AI Agent / LLM token spend in seconds — locally, read-only, with **zero cloud credentials sent to any third party**.

> **Try the Live Browser Sandbox & Interactive FinOps ROI Calculator (Zero Install):**
> - **Interactive Tool Comparison & Savings Calculator:** https://gabhack.github.io/turingtec-agent-studio/compare/aws-finops-open-source-tools/
> - **Live Agent Studio Sandbox:** https://gabhack.github.io/turingtec-agent-studio/

---

## Tier Comparison: Free Open-Core vs Pro ($49) vs Business-in-a-Box ($99)

| Capability | Free Open-Core (`$0`) | Pro Individual (`$49` one-time) | Business-in-a-Box / Team (`$99` one-time) |
|---|:---:|:---:|:---:|
| Read-only AWS & LLM/Bedrock waste audit (7 core rules) | ✅ | ✅ | ✅ |
| Local `stdio` MCP Server for Claude Desktop, Cursor & VS Code | ✅ | ✅ | ✅ |
| Zero external dependencies (`Python 3.10+` stdlib only) | ✅ | ✅ | ✅ |
| `--remediate` / `generate_terraform_remediation` HCL patches | — | ✅ | ✅ |
| Copy-paste AWS CLI cleanup commands & Executive Markdown Report | — | ✅ | ✅ |
| `--sarif` (SARIF 2.1.0) for GitHub Code Scanning & CI/CD gates | — | ✅ | ✅ |
| 14-day offline license grace cache + CI/CD env var support | — | ✅ | ✅ |
| Multi-seat team license + full B2B FinOps Agent Kit & SOP templates | — | — | ✅ |
| **Get Access** | `git clone` below | [Unlock Pro ($49)](https://gabbler407.gumroad.com/) | [Unlock Team ($99)](https://gabbler407.gumroad.com/) |

---

## Sample Terminal Output (`$510.75/mo` · `$6,129/yr` Detected Waste)

```text
$ python3 -m aws_finops_guard.cli demo

+-------------------------------------------------------------------------------------+
| AWS & AI FinOps Guard Report — demo-prod-us-east-1 (us-east-1)                      |
| Findings Detected: 7   |   Monthly Waste: $510.75/mo   |   Annual Waste: $6,129/yr  |
+-------------------------------------------------------------------------------------+
| Rule           | Severity | Resource                                  | Waste/mo    |
+----------------+----------+-------------------------------------------+-------------+
| FINOPS-LLM-001 | CRITICAL | support-triage-agent (claude-3-5-sonnet)  |   $231.00   |
| FINOPS-RDS-001 | HIGH     | db-staging-01                             |   $160.60   |
| FINOPS-NET-002 | HIGH     | nat-0123456789abcdef0 (missing S3 VPC EP) |    $52.65   |
| FINOPS-NET-001 | HIGH     | nat-0123456789abcdef1 (idle NAT GW)       |    $32.85   |
| FINOPS-EBS-001 | HIGH     | vol-0a1b2c3d4e5f002 (unattached EBS)      |    $20.00   |
| FINOPS-EBS-002 | MEDIUM   | vol-0a1b2c3d4e5f001 (legacy gp2 -> gp3)   |    $10.00   |
| FINOPS-NET-003 | LOW      | eipalloc-00112233 (unassociated EIP)      |     $3.65   |
+----------------+----------+-------------------------------------------+-------------+
| TOTAL ESTIMATED SAVINGS: $510.75 USD/mo ($6,129.00 USD/yr)                          |
+-------------------------------------------------------------------------------------+
[TIP] Unlock Terraform HCL auto-remediation & CI/CD SARIF export for $49 one-time -> https://gabbler407.gumroad.com/
```

---

## What It Detects Instantly (Free Read-Only Tier)

- **Unattached EBS Volumes (`FINOPS-EBS-001`)** & **Legacy `gp2` → `gp3` Savings (`FINOPS-EBS-002`)**
- **Idle NAT Gateways (`FINOPS-NET-001`)** & **Missing `$0` S3/DynamoDB VPC Gateway Endpoints (`FINOPS-NET-002`)**
- **Unassociated Elastic IPs (`FINOPS-NET-003`)**
- **Underutilized / Oversized Non-Prod RDS Instances (`FINOPS-RDS-001`)**
- **LLM / Bedrock / OpenAI / Gemini Token Waste (`FINOPS-LLM-001` & `FINOPS-LLM-002`):** catches classification/triage agents overpaying on premium models instead of fast-tier routing + prompt caching.

---

## Quick Start

```bash
git clone https://github.com/gabhack/aws-finops-guard.git
cd aws-finops-guard
python3 -m aws_finops_guard.cli demo
```

### Activate Pro License Key

```bash
python3 -m aws_finops_guard.cli auth YOUR-GUMROAD-LICENSE-KEY
python3 -m aws_finops_guard.cli demo --remediate -o finops-report.md
```

---

## MCP Client Configuration (Copy-Paste)

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "aws-finops-guard": {
      "command": "python3",
      "args": ["-m", "aws_finops_guard.cli", "mcp"],
      "cwd": "/absolute/path/to/aws-finops-guard",
      "env": {
        "AWS_FINOPS_GUARD_LICENSE_KEY": ""
      }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "aws-finops-guard": {
      "command": "python3",
      "args": ["-m", "aws_finops_guard.cli", "mcp"],
      "cwd": "${workspaceFolder}/aws-finops-guard"
    }
  }
}
```

### VS Code (`.vscode/mcp.json`)

```json
{
  "servers": {
    "aws-finops-guard": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "aws_finops_guard.cli", "mcp"],
      "cwd": "${workspaceFolder}/aws-finops-guard"
    }
  }
}
```

### AI Setup Assistant Prompt (Paste into Claude or Cursor)

Paste this prompt into Claude Code, Cursor, or your coding assistant to install and configure `aws-finops-guard` automatically:

```text
Clone https://github.com/gabhack/aws-finops-guard.git into a local folder, verify Python 3.10+ is available, run `python3 -m aws_finops_guard.cli demo` to confirm it outputs the $510.75/mo ($6,129/yr) sample audit, and add the `aws-finops-guard` stdio MCP server entry to my MCP config file with the absolute `cwd` path. Do not send any AWS credentials to external services.
```

---

## Multi-Registry Metadata

This repository ships with complete MCP registry manifests:
- [`server.json`](./server.json) — Official MCP Registry manifest (`io.github.gabhack/aws-finops-guard`)
- [`glama.json`](./glama.json) — Glama MCP Directory manifest
- [`smithery.yaml`](./smithery.yaml) — Smithery MCP Registry manifest

---

## Built by TuringTec Agent Studio

- **Interactive FinOps Tool Comparison & ROI Calculator:** https://gabhack.github.io/turingtec-agent-studio/compare/aws-finops-open-source-tools/
- **Interactive Demos & B2B AI Agent Kits:** https://gabhack.github.io/turingtec-agent-studio/
- **Apify Dual-Mode MCP Server Suite:** https://github.com/gabhack/apify-cloud-mcp-suite
- **Multi-Cloud & AI Certification Simulator (CloudCert Lab):** https://gabhack.github.io/cloudcert-lab/
