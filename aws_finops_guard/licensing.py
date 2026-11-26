#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gumroad License Key Verification with 14-day local offline grace cache.
Uses POST https://api.gumroad.com/v2/licenses/verify (zero backend server required).
"""

from __future__ import annotations

import datetime
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

LICENSE_FILE = Path.home() / ".config" / "aws-finops-guard" / "license.json"
GUMROAD_PRODUCT_ID = os.environ.get("AWS_FINOPS_GUMROAD_PRODUCT_ID", "aws-finops-guard-pro")
GUMROAD_CHECKOUT_URL = "https://gabbler407.gumroad.com/"
OFFLINE_GRACE_DAYS = 14


def verify_license_remote(license_key: str, product_id: str | None = None, increment_uses: bool = True) -> dict[str, Any]:
    pid = product_id or GUMROAD_PRODUCT_ID
    data = urllib.parse.urlencode(
        {
            "product_id": pid,
            "license_key": license_key.strip(),
            "increment_uses_count": "true" if increment_uses else "false",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.gumroad.com/v2/licenses/verify",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "aws-finops-guard/0.1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    purchase = payload.get("purchase", {}) or {}
    valid = bool(payload.get("success")) and not purchase.get("refunded") and not purchase.get("disputed") and not purchase.get("chargebacked")
    return {"valid": valid, "uses": payload.get("uses", 0), "email": purchase.get("email", ""), "raw": payload}


def save_license_cache(license_key: str, email: str = "") -> None:
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "license_key": license_key.strip(),
        "email": email,
        "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    LICENSE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def has_active_pro_license() -> tuple[bool, str]:
    # Support CI/CD env var override or cached local license within 14-day grace window
    env_key = os.environ.get("AWS_FINOPS_GUARD_LICENSE_KEY", "").strip()
    if env_key:
        try:
            res = verify_license_remote(env_key, increment_uses=False)
            if res["valid"]:
                return (True, "Verified via AWS_FINOPS_GUARD_LICENSE_KEY")
        except Exception:
            pass
    if LICENSE_FILE.exists():
        try:
            rec = json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
            ts = datetime.datetime.fromisoformat(rec["verified_at"])
            age_days = (datetime.datetime.now(datetime.timezone.utc) - ts).days
            if age_days <= OFFLINE_GRACE_DAYS:
                return (True, f"Active local Pro license ({rec.get('email') or 'cached'}, {OFFLINE_GRACE_DAYS - age_days}d grace left)")
            res = verify_license_remote(rec["license_key"], increment_uses=False)
            if res["valid"]:
                save_license_cache(rec["license_key"], res.get("email", ""))
                return (True, "Re-verified Pro license via Gumroad API")
        except Exception:
            pass
    return (False, f"Pro feature locked. Unlock Terraform auto-remediation & SARIF export at {GUMROAD_CHECKOUT_URL}")
