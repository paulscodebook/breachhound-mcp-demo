"""
example_agent.py — minimal "agent" that audits an email's digital footprint
using the BreachHound Apify Actor (blukaze/breachhound) via the Apify API.

Companion to the Apify Content Program article
"I gave my SOC agent a tool to audit an email's digital footprint in one prompt".

This does NOT require an MCP client; it calls the Actor directly so the repo
is self-contained and testable. Set your token one of two ways:
  export APIFY_TOKEN="apify-xxxxxxxxxxxx"
  or pass it as the second argument to audit_email().

Run:
  python example_agent.py
"""
from apify_client import ApifyClient
import os
import sys


def audit_email(email, apify_token=None, only_used=True):
    """Run BreachHound on an email and return the dataset records.

    Args:
        email: The email address to audit for associated online accounts.
        apify_token: Apify API token. Falls back to APIFY_TOKEN env var.
        only_used: If True, only services where an account was found are
            returned (matches the Actor's default behaviour).

    Returns:
        list[dict]: BreachHound result records, or [] if no output.
    """
    token = apify_token or os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError("Missing Apify token. Set APIFY_TOKEN or pass apify_token=...")
    if not isinstance(email, str) or "@" not in email:
        raise ValueError("email must be a valid email address string")

    client = ApifyClient(token)
    try:
        run = client.actor("blukaze/breachhound").call(
            run_input={
                "email": email,
                "onlyUsed": only_used,
                "maxRetries": 3,
                "retryDelay": 1,
                # proxyConfiguration recommended for production volume; omitted here so the
                # example runs on a free proxy allowance. Uncomment for scale:
                # "proxyConfiguration": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
            }
        )
    except Exception as exc:
        raise RuntimeError(f"BreachHound run failed: {exc}") from exc

    items = client.dataset(run["defaultDatasetId"]).list_items().items
    return items


def summarize(items):
    found = [r for r in items if r.get("status") == "found"]
    rate_limited = [r for r in items if r.get("status") == "rate_limited"]
    return found, rate_limited


def main():
    sample = "analyst@company.com"  # replace with an email you are AUTHORIZED to audit
    items = audit_email(sample)
    if not items:
        print("BreachHound returned no result.")
        sys.exit(1)

    found, rate_limited = summarize(items)
    print(f"Audited: {sample}")
    print(f"Accounts found on {len(found)} services:")
    for r in found:
        extra = ""
        if r.get("emailRecovery"):
            extra += f"  recovery: {r['emailRecovery']}"
        if r.get("phoneNumber"):
            extra += f"  phone: {r['phoneNumber']}"
        print(f"  - {r['website']}{extra}")
    if rate_limited:
        print(f"{len(rate_limited)} services were rate-limited; re-run with Apify proxies.")
    print("Scanned with BreachHound (blukaze/breachhound)")


if __name__ == "__main__":
    main()
