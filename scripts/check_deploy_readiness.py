#!/usr/bin/env python3
"""Check whether local configuration is production-deployment ready."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
BACKEND_ENV_EXAMPLE = REPO_ROOT / "backend" / ".env.example"
FRONTEND_ENV_EXAMPLE = REPO_ROOT / "frontend" / ".env.local.example"
MOBILE_ENV_EXAMPLE = REPO_ROOT / "mobile" / ".env.example"

PLACEHOLDER_PATTERNS = (
    r"^test_",
    r"your_",
    r"example\\.com",
    r"^password$",
    r"^supersecret",
)


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(re.search(pattern, lowered) for pattern in PLACEHOLDER_PATTERNS)


def bool_env(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    using_example_env = False
    if not BACKEND_ENV.exists():
        using_example_env = True
        warnings.append(
            "backend/.env is missing. Copy backend/.env.example to backend/.env and set real secrets before deployment."
        )
        env = parse_env(BACKEND_ENV_EXAMPLE)
    else:
        env = parse_env(BACKEND_ENV)

    for required_file in (FRONTEND_ENV_EXAMPLE, MOBILE_ENV_EXAMPLE, BACKEND_ENV_EXAMPLE):
        if not required_file.exists():
            errors.append(f"Required template file missing: {required_file.relative_to(REPO_ROOT)}")

    required_keys = (
        "PROJECT_NAME",
        "APP_INSTANCE_NAME",
        "SECRET_KEY",
        "DATABASE_URL",
        "FRONTEND_URL",
        "SERVER_HOST",
    )

    for key in required_keys:
        value = env.get(key, "")
        if not value:
            errors.append(f"{key} is missing or empty")
        elif is_placeholder(value):
            if using_example_env:
                warnings.append(f"{key} in backend/.env.example is placeholder-like ({value!r}); replace in backend/.env")
            else:
                errors.append(f"{key} is using a placeholder value ({value!r})")

    provider_requirements: dict[str, tuple[str, ...]] = {
        "EMAIL_ENABLED": ("EMAIL_FROM_ADDRESS",),
        "STRIPE_ENABLED": ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"),
        "PAYPAL_ENABLED": ("PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"),
        "GOOGLE_ENABLED": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
        "GITHUB_ENABLED": ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"),
        "FACEBOOK_ENABLED": ("FACEBOOK_CLIENT_ID", "FACEBOOK_CLIENT_SECRET"),
    }

    for feature_flag, keys in provider_requirements.items():
        if not bool_env(env.get(feature_flag)):
            continue
        for key in keys:
            value = env.get(key, "")
            if not value:
                errors.append(f"{feature_flag}=true but {key} is empty")
            elif is_placeholder(value):
                if using_example_env:
                    warnings.append(
                        f"{feature_flag}=true and {key} in backend/.env.example is placeholder-like ({value!r}); replace in backend/.env"
                    )
                else:
                    errors.append(f"{feature_flag}=true but {key} is placeholder-like ({value!r})")

    if errors:
        print("Deployment readiness check failed:")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")
        return 1

    if warnings:
        print("Deployment readiness check passed with warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 0

    print("Deployment readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
