#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic AWS + LLM/Bedrock FinOps Audit Engine (Zero External Dependencies).
Analyzes local AWS resource/cost snapshots or Terraform JSON plans to detect
monthly USD waste and generate safe remediation patches (Terraform + AWS CLI).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

LLM_PRICING_PER_1M = {
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "tier": "premium"},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00, "tier": "fast"},
    "gpt-4o": {"input": 2.50, "output": 10.00, "tier": "premium"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "tier": "fast"},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00, "tier": "premium"},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "tier": "fast"},
    "amazon-nova-pro": {"input": 0.80, "output": 3.20, "tier": "balanced"},
    "amazon-nova-lite": {"input": 0.06, "output": 0.24, "tier": "fast"},
}

SAMPLE_SNAPSHOT: dict[str, Any] = {
    "account_alias": "demo-prod-us-east-1",
    "region": "us-east-1",
    "ebs_volumes": [
        {"id": "vol-0a1b2c3d4e5f001", "type": "gp2", "size_gb": 500, "state": "in-use", "tags": {"Env": "prod"}},
        {"id": "vol-0a1b2c3d4e5f002", "type": "gp3", "size_gb": 250, "state": "available", "tags": {}},
    ],
    "nat_gateways": [
        {"id": "nat-0123456789abcdef0", "avg_gb_per_month": 1800, "has_s3_gateway_endpoint": False},
        {"id": "nat-0123456789abcdef1", "avg_gb_per_month": 0.4, "has_s3_gateway_endpoint": True},
    ],
    "elastic_ips": [
        {"allocation_id": "eipalloc-00112233", "associated": False},
        {"allocation_id": "eipalloc-00112244", "associated": True},
    ],
    "rds_instances": [
        {"id": "db-staging-01", "instance_class": "db.m5.xlarge", "avg_cpu_pct": 6.5, "monthly_cost_usd": 292.0, "env": "staging"},
    ],
    "llm_workloads": [
        {
            "name": "support-triage-agent",
            "model": "claude-3-5-sonnet",
            "monthly_input_millions": 45.0,
            "monthly_output_millions": 12.0,
            "prompt_cache_enabled": False,
            "task_complexity": "classification",
        }
    ],
}


@dataclass
class Finding:
    rule_id: str
    severity: str
    category: str
    resource: str
    monthly_waste_usd: float
    summary: str
    recommendation: str
    terraform_patch: str
    cli_command: str


def audit_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    findings: list[Finding] = []
    region = snapshot.get("region", "us-east-1")

    # 1. EBS Volumes (unattached or legacy gp2)
    for vol in snapshot.get("ebs_volumes", []):
        vid = str(vol.get("id", "vol-unknown"))
        vtype = str(vol.get("type", "gp3")).lower()
        size_gb = float(vol.get("size_gb", 0) or 0)
        state = str(vol.get("state", "in-use")).lower()
        if state == "available" and size_gb > 0:
            waste = round(size_gb * (0.10 if vtype == "gp2" else 0.08), 2)
            findings.append(
                Finding(
                    rule_id="FINOPS-EBS-001",
                    severity="HIGH",
                    category="AWS Storage",
                    resource=vid,
                    monthly_waste_usd=waste,
                    summary=f"Unattached EBS volume ({size_gb:.0f} GB {vtype}) incurring ${waste:.2f}/mo.",
                    recommendation="Create final snapshot if needed and delete unattached EBS volume.",
                    terraform_patch=f'# Remove orphaned aws_ebs_volume "{vid}" after taking snapshot\n# terraform state rm aws_ebs_volume.{vid.replace("-", "_")}',
                    cli_command=f"aws ec2 create-snapshot --region {region} --volume-id {vid} && aws ec2 delete-volume --region {region} --volume-id {vid}",
                )
            )
        elif vtype == "gp2" and size_gb >= 50:
            waste = round(size_gb * 0.02, 2)
            findings.append(
                Finding(
                    rule_id="FINOPS-EBS-002",
                    severity="MEDIUM",
                    category="AWS Storage",
                    resource=vid,
                    monthly_waste_usd=waste,
                    summary=f"Legacy gp2 EBS volume ({size_gb:.0f} GB) costs 20% more than gp3 (+${waste:.2f}/mo).",
                    recommendation="Migrate online with zero downtime from gp2 to gp3.",
                    terraform_patch=f'resource "aws_ebs_volume" "{vid.replace("-", "_")}" {{\n  type = "gp3"\n  size = {int(size_gb)}\n}}',
                    cli_command=f"aws ec2 modify-volume --region {region} --volume-id {vid} --volume-type gp3",
                )
            )

    # 2. NAT Gateways (idle or missing S3/DynamoDB Gateway Endpoints)
    for nat in snapshot.get("nat_gateways", []):
        nid = str(nat.get("id", "nat-unknown"))
        gb = float(nat.get("avg_gb_per_month", 0) or 0)
        has_ep = bool(nat.get("has_s3_gateway_endpoint", True))
        if gb < 5.0:
            waste = 32.85
            findings.append(
                Finding(
                    rule_id="FINOPS-NET-001",
                    severity="HIGH",
                    category="AWS Networking",
                    resource=nid,
                    monthly_waste_usd=waste,
                    summary=f"Idle NAT Gateway ({gb:.1f} GB/mo) burning ${waste:.2f}/mo base hourly charge.",
                    recommendation="Delete unused NAT Gateway or consolidate single-AZ NAT in non-prod VPCs.",
                    terraform_patch=f'# Remove idle aws_nat_gateway "{nid}" and update non-prod route tables',
                    cli_command=f"aws ec2 delete-nat-gateway --region {region} --nat-gateway-id {nid}",
                )
            )
        elif not has_ep and gb >= 100:
            s3_gb = gb * 0.65
            waste = round(s3_gb * 0.045, 2)
            findings.append(
                Finding(
                    rule_id="FINOPS-NET-002",
                    severity="HIGH",
                    category="AWS Networking",
                    resource=nid,
                    monthly_waste_usd=waste,
                    summary=f"NAT Gateway processing {gb:.0f} GB/mo without S3 Gateway Endpoint (~${waste:.2f}/mo avoidable).",
                    recommendation="Attach a $0 AWS VPC Gateway Endpoint for S3 and DynamoDB.",
                    terraform_patch='resource "aws_vpc_endpoint" "s3_gateway" {\n  vpc_id            = var.vpc_id\n  service_name      = "com.amazonaws.' + region + '.s3"\n  vpc_endpoint_type = "Gateway"\n  route_table_ids   = var.private_route_table_ids\n}',
                    cli_command=f"aws ec2 create-vpc-endpoint --region {region} --vpc-id <VPC_ID> --service-name com.amazonaws.{region}.s3 --vpc-endpoint-type Gateway",
                )
            )

    # 3. Unattached Elastic IPs
    for eip in snapshot.get("elastic_ips", []):
        if not eip.get("associated", True):
            aid = str(eip.get("allocation_id", "eipalloc-unknown"))
            waste = 3.65
            findings.append(
                Finding(
                    rule_id="FINOPS-NET-003",
                    severity="LOW",
                    category="AWS Networking",
                    resource=aid,
                    monthly_waste_usd=waste,
                    summary=f"Unassociated Elastic IP ({aid}) billed at $0.005/hr (${waste:.2f}/mo).",
                    recommendation="Release unused Elastic IP immediately.",
                    terraform_patch=f'# Remove unused aws_eip "{aid}" resource block',
                    cli_command=f"aws ec2 release-address --region {region} --allocation-id {aid}",
                )
            )

    # 4. Oversized / Idle RDS
    for db in snapshot.get("rds_instances", []):
        dbid = str(db.get("id", "db-unknown"))
        cpu = float(db.get("avg_cpu_pct", 50) or 50)
        cost = float(db.get("monthly_cost_usd", 0) or 0)
        env = str(db.get("env", "prod")).lower()
        if cpu < 15.0 and cost >= 80:
            factor = 0.55 if env != "prod" else 0.35
            waste = round(cost * factor, 2)
            findings.append(
                Finding(
                    rule_id="FINOPS-RDS-001",
                    severity="HIGH",
                    category="AWS Databases",
                    resource=dbid,
                    monthly_waste_usd=waste,
                    summary=f"Underutilized RDS ({db.get('instance_class')}, {cpu:.1f}% CPU, ${cost:.0f}/mo) wastes ~${waste:.2f}/mo.",
                    recommendation="Downsize instance class or switch non-prod to Aurora Serverless v2 with scale-to-zero.",
                    terraform_patch=f'resource "aws_db_instance" "{dbid.replace("-", "_")}" {{\n  instance_class = "db.t4g.medium"\n}}',
                    cli_command=f"aws rds modify-db-instance --region {region} --db-instance-identifier {dbid} --db-instance-class db.t4g.medium --apply-immediately",
                )
            )

    # 5. LLM / Bedrock Agent Token Optimization
    for wl in snapshot.get("llm_workloads", []):
        name = str(wl.get("name", "llm-agent"))
        model = str(wl.get("model", "claude-3-5-sonnet")).lower()
        in_m = float(wl.get("monthly_input_millions", 0) or 0)
        out_m = float(wl.get("monthly_output_millions", 0) or 0)
        cached = bool(wl.get("prompt_cache_enabled", False))
        complexity = str(wl.get("task_complexity", "general")).lower()
        pricing = LLM_PRICING_PER_1M.get(model)
        if not pricing or (in_m + out_m) <= 0:
            continue
        current_cost = round(in_m * pricing["input"] + out_m * pricing["output"], 2)
        if pricing["tier"] == "premium" and complexity in ("classification", "extraction", "routing", "triage"):
            fast_model = "gemini-2.5-flash" if "gemini" in model else ("amazon-nova-lite" if "nova" in model else "claude-3-5-haiku")
            fp = LLM_PRICING_PER_1M[fast_model]
            new_cost = round(in_m * fp["input"] + out_m * fp["output"], 2)
            waste = round(max(0.0, current_cost - new_cost), 2)
            if waste >= 10.0:
                findings.append(
                    Finding(
                        rule_id="FINOPS-LLM-001",
                        severity="CRITICAL",
                        category="AI / LLM FinOps",
                        resource=f"{name} ({model})",
                        monthly_waste_usd=waste,
                        summary=f"Premium model '{model}' used for {complexity} (${current_cost:.2f}/mo vs ${new_cost:.2f}/mo on '{fast_model}').",
                        recommendation=f"Route {complexity} turns to '{fast_model}' and enable prompt caching for system instructions.",
                        terraform_patch=f'# Tiered model routing env var for {name}\nLLM_ROUTER_FAST_MODEL="{fast_model}"\nLLM_PROMPT_CACHE_ENABLED="true"',
                        cli_command=f"# Update agent config: set model={fast_model} & enable prompt_caching=true (est. savings ${waste:.2f}/mo)",
                    )
                )
        elif not cached and in_m >= 10.0:
            waste = round(in_m * pricing["input"] * 0.45, 2)
            findings.append(
                Finding(
                    rule_id="FINOPS-LLM-002",
                    severity="MEDIUM",
                    category="AI / LLM FinOps",
                    resource=f"{name} ({model})",
                    monthly_waste_usd=waste,
                    summary=f"Prompt caching disabled on {in_m:.1f}M input tokens/mo (~${waste:.2f}/mo avoidable input cost).",
                    recommendation="Enable Bedrock / Anthropic / Gemini Context Caching for repeated system prompts & RAG headers.",
                    terraform_patch=f'# Enable context caching on {name}\nLLM_PROMPT_CACHE_ENABLED="true"',
                    cli_command=f"# Enable prompt caching on {name} (est. savings ${waste:.2f}/mo)",
                )
            )

    total_monthly = round(sum(f.monthly_waste_usd for f in findings), 2)
    total_annual = round(total_monthly * 12.0, 2)
    return {
        "account_alias": snapshot.get("account_alias", "unknown"),
        "region": region,
        "findings_count": len(findings),
        "estimated_monthly_savings_usd": total_monthly,
        "estimated_annual_savings_usd": total_annual,
        "findings": [asdict(f) for f in findings],
    }


def render_markdown_report(result: dict[str, Any], include_remediation: bool = False) -> str:
    lines = [
        f"# AWS & AI FinOps Guard Report — `{result['account_alias']}` (`{result['region']}`)",
        "",
        f"- **Findings Detected:** `{result['findings_count']}`",
        f"- **Estimated Monthly Savings:** **`${result['estimated_monthly_savings_usd']:,.2f} USD/mo`**",
        f"- **Estimated Annual Savings:** **`${result['estimated_annual_savings_usd']:,.2f} USD/yr`**",
        "",
        "## Findings Breakdown",
        "",
        "| Rule | Severity | Resource | Monthly Waste | Recommendation |",
        "|---|---|---|---:|---|",
    ]
    for f in result["findings"]:
        lines.append(
            f"| `{f['rule_id']}` | **{f['severity']}** | `{f['resource']}` | `${f['monthly_waste_usd']:,.2f}` | {f['recommendation']} |"
        )
    if include_remediation:
        lines.extend(["", "## Safe Remediation Patches (Terraform & AWS CLI)", ""])
        for f in result["findings"]:
            lines.append(f"### {f['rule_id']} — `{f['resource']}` (`${f['monthly_waste_usd']:,.2f}/mo`)")
            lines.append("```hcl")
            lines.append(f["terraform_patch"])
            lines.append("```")
            lines.append("```bash")
            lines.append(f["cli_command"])
            lines.append("```")
            lines.append("")
    return "\n".join(lines) + "\n"


def render_sarif(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "aws-finops-guard",
                        "version": "0.1.0",
                        "informationUri": "https://gabhack.github.io/turingtec-agent-studio/",
                    }
                },
                "results": [
                    {
                        "ruleId": f["rule_id"],
                        "level": "error" if f["severity"] in ("CRITICAL", "HIGH") else "warning",
                        "message": {"text": f"{f['summary']} Recommendation: {f['recommendation']}"},
                        "locations": [{"physicalLocation": {"artifactLocation": {"uri": f["resource"]}}}],
                    }
                    for f in result["findings"]
                ],
            }
        ],
    }
