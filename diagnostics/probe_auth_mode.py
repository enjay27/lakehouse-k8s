#!/usr/bin/env python3
"""
probe_auth_mode.py — Step 0 of the Spark token-TTL / refresh investigation.

READ-ONLY. Creates nothing, deletes nothing, changes no server config.
Safe to run against any environment including prod (same posture as
`availability/`), which is why it carries no `require_not_prod()` guard.

WHY THIS EXISTS
---------------
The Spark token-expiry tests (TTL=1m, long job, auto-refresh) are only
meaningful if we know WHO mints the token that Spark carries:

  * Polaris internal token broker  -> TTL is a Polaris server property, and
    the refresh story is whatever Polaris's own /v1/oauth/tokens supports.
  * External IdP (Keycloak/OIDC)   -> TTL lives in the Keycloak realm/client,
    and refresh depends on Keycloak's enabled grants + client toggles.

Production is Keycloak. If LOCAL is on the internal broker, then any result
measured locally describes a different auth stack than the one we care about.
This probe decides that before we build anything on top of it.

WHAT IT REPORTS
---------------
  1. Whether Polaris's internal OAuth2 token endpoint still answers.
  2. The token's `iss` claim -- the decisive "who issued this" signal.
  3. Measured TTL (`exp - iat`) in seconds.
  4. Whether a refresh_token is issued for the client_credentials grant.
     (RFC 6749 4.4.3 says it SHOULD NOT be; Keycloak's per-client toggle for
     this is off by default. If absent, "automatic refresh" cannot mean
     "refresh_token grant" -- it must mean re-auth or token-exchange.)
  5. The OIDC discovery document, if the issuer publishes one:
     `grant_types_supported` tells us whether token-exchange (which is what
     Iceberg's built-in OAuth2 refresh actually issues) is even available.
  6. The `WWW-Authenticate` challenge on a rejected token -- often names the
     external realm even when nothing else does.
  7. Optionally (--expiry-check): sleeps past `exp` and re-calls the catalog
     API to confirm the server actually ENFORCES expiry rather than merely
     stamping it. Skipped by default because with a 1h TTL it takes an hour.

USAGE
-----
    python diagnostics/probe_auth_mode.py
    python diagnostics/probe_auth_mode.py --env local
    python diagnostics/probe_auth_mode.py --expiry-check          # after TTL=1m
    python diagnostics/probe_auth_mode.py \
        --token-endpoint https://keycloak.example/realms/r/protocol/openid-connect/token \
        --client-id spark-engine                                  # secret via env

CREDENTIALS
-----------
Never passed on the command line. Defaults come from `init_env()`
(`src/config/<env>.yaml`, gitignored). To probe a non-root client, set
`--client-id` and export `PROBE_CLIENT_SECRET`.
"""

import argparse
import base64
import json
import os
import pathlib
import sys
import time

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import polaris_test_utils as ptu  # noqa: E402

TIMEOUT = (5, 30)  # connect, read -- same posture as the notebook bootstrap


# ── output helpers ────────────────────────────────────────────
def head(title):
    print(f"\n{'=' * 68}\n{title}\n{'=' * 68}")


def kv(key, value):
    print(f"  {key:<28} {value}")


def redact(secret_ish, keep=6):
    """Show enough of a token to correlate across logs, never enough to use."""
    if not secret_ish:
        return "<none>"
    s = str(secret_ish)
    return f"{s[:keep]}...{s[-4:]} (len={len(s)})" if len(s) > keep + 8 else "<short>"


# ── JWT decoding (no signature verification -- inspection only) ──
def decode_jwt(token):
    """Split a JWS compact token and base64url-decode header + payload.

    Deliberately does NOT verify the signature: we have no key material here
    and the goal is to read claims, not to trust them. Returns
    (header, payload) or (None, None) if the token isn't a decodable JWT --
    an opaque token is itself a finding worth reporting.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None, None
        out = []
        for seg in parts[:2]:
            pad = "=" * (-len(seg) % 4)
            out.append(json.loads(base64.urlsafe_b64decode(seg + pad)))
        return out[0], out[1]
    except Exception:
        return None, None


def classify_issuer(iss, polaris_url):
    """Best-effort read of the `iss` claim. Heuristic, and says so."""
    if not iss:
        return "UNKNOWN -- no `iss` claim (Polaris's internal broker may omit it)"
    low = iss.lower()
    if "/realms/" in low:
        return "EXTERNAL IdP -- Keycloak (issuer contains /realms/)"
    if polaris_url and polaris_url.split("//")[-1].split(":")[0] in low:
        return "INTERNAL -- issuer is the Polaris host itself"
    if "polaris" in low:
        return "INTERNAL -- Polaris token broker"
    return "EXTERNAL IdP (non-Keycloak, or unrecognised issuer)"


# ── probes ────────────────────────────────────────────────────
def probe_internal_token_endpoint(
    token_endpoint, realm, client_id, client_secret, scope
):
    """POST client_credentials. Returns (response|None, error_string|None).

    A non-200 here is a RESULT, not a failure: if Polaris is configured for
    external-only authentication its internal broker is expected to refuse.
    """
    head("1. client_credentials against the token endpoint")
    kv("endpoint", token_endpoint)
    kv("client_id", client_id)
    kv("realm header", realm or "<not sent>")
    headers = {"Polaris-Realm": realm} if realm else {}
    try:
        r = requests.post(
            token_endpoint,
            headers=headers,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        kv("RESULT", f"UNREACHABLE -- {type(e).__name__}: {e}")
        return None, str(e)

    kv("status", r.status_code)
    if r.status_code != 200:
        body = r.text[:400]
        kv("body", body)
        if r.status_code in (404, 405, 501):
            kv(
                "READING",
                "endpoint absent/disabled -> Polaris is likely EXTERNAL-ONLY "
                "(polaris.authentication.type=external)",
            )
        elif r.status_code in (400, 401):
            kv(
                "READING",
                "endpoint exists but rejected these credentials -- could be bad "
                "creds OR external-only mode. Check the body text above.",
            )
        return r, None
    return r, None


def report_token_response(r):
    """Read the token response body: TTL, refresh_token presence, claims."""
    head("2. Token response body")
    try:
        body = r.json()
    except ValueError:
        kv("RESULT", "non-JSON response body -- unexpected")
        print(r.text[:400])
        return None

    kv("keys returned", ", ".join(sorted(body.keys())))
    kv("token_type", body.get("token_type"))
    kv("access_token", redact(body.get("access_token")))

    expires_in = body.get("expires_in")
    kv("expires_in", expires_in if expires_in is not None else "<ABSENT>")
    if expires_in is None:
        kv(
            "READING",
            "no `expires_in` -> an Iceberg REST client has nothing to schedule "
            "a refresh from. Auto-refresh cannot work. This alone would decide "
            "test 2.",
        )

    rt = body.get("refresh_token")
    kv("refresh_token", redact(rt) if rt else "<ABSENT>")
    kv(
        "READING",
        (
            "refresh_token IS issued -- a refresh_token grant is possible."
            if rt
            else "no refresh_token (expected for client_credentials; RFC 6749 "
            "4.4.3). 'Automatic refresh' must therefore be either "
            "token-exchange or plain re-auth -- not a refresh_token grant."
        ),
    )
    return body


def report_claims(token, polaris_url):
    """Decode and report the claims that identify the issuer and the TTL."""
    head("3. Access-token claims (decoded, signature NOT verified)")
    header, payload = decode_jwt(token)
    if payload is None:
        kv("RESULT", "not a decodable JWT -- opaque token")
        kv(
            "READING",
            "opaque tokens must be introspected server-side; Polaris would need "
            "the IdP's introspection endpoint. Worth confirming separately.",
        )
        return None

    kv("alg", header.get("alg"))
    kv("kid", header.get("kid", "<none>"))
    if header.get("kid"):
        kv(
            "NOTE",
            "`kid` present -> signature keys come from a JWKS endpoint. Key "
            "rotation vs. Polaris's JWKS cache is a production concern.",
        )

    iss = payload.get("iss")
    kv("iss", iss or "<none>")
    kv("VERDICT", classify_issuer(iss, polaris_url))
    for claim in ("sub", "aud", "azp", "client_id", "scope", "typ", "realm"):
        if claim in payload:
            kv(claim, payload[claim])

    iat, exp = payload.get("iat"), payload.get("exp")
    if iat and exp:
        ttl = exp - iat
        kv("iat", f"{iat}  ({time.strftime('%H:%M:%S', time.localtime(iat))})")
        kv("exp", f"{exp}  ({time.strftime('%H:%M:%S', time.localtime(exp))})")
        kv("MEASURED TTL", f"{ttl}s  ({ttl / 60:.1f} min)")
        skew = int(time.time()) - iat
        kv("local clock vs iat", f"{skew:+d}s")
        if abs(skew) > 30:
            kv(
                "WARNING",
                "clock skew > 30s between this machine and the issuer. With a "
                "60s TTL that is a large fraction of the token's life and will "
                "produce intermittent, hard-to-reproduce 401s.",
            )
    else:
        kv("MEASURED TTL", "<cannot compute -- iat/exp missing>")
    return payload


def probe_discovery(iss):
    """Fetch the OIDC discovery doc. Reveals which grants are actually usable."""
    head("4. OIDC discovery (grants available for refresh)")
    if not iss or not iss.startswith("http"):
        kv("RESULT", "skipped -- no http(s) issuer claim to discover from")
        return None
    url = iss.rstrip("/") + "/.well-known/openid-configuration"
    kv("url", url)
    try:
        r = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        kv("RESULT", f"unreachable -- {type(e).__name__}: {e}")
        kv(
            "NOTE",
            "if the issuer URL is only resolvable from inside the cluster, run "
            "this probe from a pod or port-forward the IdP.",
        )
        return None

    kv("status", r.status_code)
    if r.status_code != 200:
        kv("RESULT", "no discovery document at the issuer")
        return None

    doc = r.json()
    kv("token_endpoint", doc.get("token_endpoint"))
    kv("jwks_uri", doc.get("jwks_uri"))
    grants = doc.get("grant_types_supported", [])
    kv("grant_types_supported", ", ".join(grants) if grants else "<not advertised>")

    tx = "urn:ietf:params:oauth:grant-type:token-exchange"
    kv(
        "token-exchange",
        "ADVERTISED" if tx in grants else "NOT advertised",
    )
    kv(
        "READING",
        (
            "Iceberg's built-in OAuth2 refresh issues a token-exchange request. "
            "Advertised here, so that path is at least possible -- still needs "
            "per-client permissions in Keycloak."
            if tx in grants
            else "Iceberg's built-in OAuth2 refresh issues a token-exchange "
            "request. Not advertised -> that path will fail, and any observed "
            "refresh must be plain re-auth instead."
        ),
    )
    kv(
        "refresh_token grant",
        "advertised" if "refresh_token" in grants else "not advertised",
    )
    return doc


def probe_rejected_token(polaris_url, realm):
    """Send a deliberately invalid bearer token; read the challenge header."""
    head("5. Rejection behaviour (WWW-Authenticate challenge)")
    url = f"{polaris_url}/api/management/v1/principal-roles"
    headers = {"Authorization": "Bearer not-a-real-token"}
    if realm:
        headers["Polaris-Realm"] = realm
    kv("url", url)
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        kv("RESULT", f"unreachable -- {type(e).__name__}: {e}")
        return
    kv("status", r.status_code)
    challenge = r.headers.get("WWW-Authenticate")
    kv("WWW-Authenticate", challenge or "<none>")
    if challenge and "realm" in challenge.lower():
        kv(
            "READING",
            "the challenge names a realm -- often identifies the external IdP",
        )
    kv("body", r.text[:200])


def probe_expiry_enforcement(polaris_url, realm, token, exp):
    """Sleep past `exp`, then reuse the token. Confirms enforcement, not stamping."""
    head("6. Expiry enforcement (--expiry-check)")
    if not exp:
        kv("RESULT", "skipped -- no `exp` claim to wait on")
        return
    wait = int(exp - time.time()) + 5
    if wait > 300:
        kv(
            "RESULT",
            f"skipped -- {wait}s until expiry (>5 min). Lower the TTL first, "
            "then re-run with --expiry-check.",
        )
        return

    url = f"{polaris_url}/api/management/v1/principal-roles"
    headers = {"Authorization": f"Bearer {token}"}
    if realm:
        headers["Polaris-Realm"] = realm

    before = requests.get(url, headers=headers, timeout=TIMEOUT)
    kv("before expiry", f"status {before.status_code}")
    if before.status_code != 200:
        kv(
            "WARNING",
            "token was already not working BEFORE expiry -- the post-expiry "
            "result below proves nothing. Investigate the pre-expiry failure.",
        )

    kv("sleeping", f"{wait}s (until 5s past exp)")
    time.sleep(max(wait, 0))

    after = requests.get(url, headers=headers, timeout=TIMEOUT)
    kv("after expiry", f"status {after.status_code}")
    kv("body", after.text[:200])
    kv(
        "VERDICT",
        (
            "ENFORCED -- expired token rejected. The TTL is real and the Spark "
            "test will exercise a genuine expiry."
            if after.status_code in (401, 403)
            else f"NOT ENFORCED -- expired token still returned "
            f"{after.status_code}. Any 'long job succeeded' result would be "
            "meaningless; fix this before running the Spark test."
        ),
    )


# ── main ──────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="Probe Polaris's authentication mode (read-only)."
    )
    ap.add_argument("--env", default="local", help="init_env target (default: local)")
    ap.add_argument("--token-endpoint", help="override; e.g. Keycloak's token endpoint")
    ap.add_argument("--client-id", help="override; secret via PROBE_CLIENT_SECRET")
    ap.add_argument("--scope", default="PRINCIPAL_ROLE:ALL")
    ap.add_argument(
        "--no-realm-header",
        action="store_true",
        help="omit Polaris-Realm (external IdP)",
    )
    ap.add_argument(
        "--expiry-check",
        action="store_true",
        help="sleep past exp and retry (needs short TTL)",
    )
    args = ap.parse_args()

    head(f"Polaris auth-mode probe  --  env={args.env}  --  READ-ONLY")
    ptu.init_env(args.env)
    polaris_url = ptu.POLARIS_URL
    realm = None if args.no_realm_header else ptu.REALM
    kv("POLARIS_URL", polaris_url)
    kv("REALM", ptu.REALM)

    client_id = args.client_id or ptu.ROOT_CLIENT
    client_secret = os.environ.get("PROBE_CLIENT_SECRET") or (
        None if args.client_id else ptu.ROOT_SECRET
    )
    if not client_secret:
        sys.exit(
            "ERROR: --client-id given without PROBE_CLIENT_SECRET in the environment."
        )

    token_endpoint = args.token_endpoint or f"{polaris_url}/api/catalog/v1/oauth/tokens"

    r, err = probe_internal_token_endpoint(
        token_endpoint, realm, client_id, client_secret, args.scope
    )

    payload = None
    if r is not None and r.status_code == 200:
        body = report_token_response(r)
        if body and body.get("access_token"):
            payload = report_claims(body["access_token"], polaris_url)
            if payload:
                probe_discovery(payload.get("iss"))

    probe_rejected_token(polaris_url, realm)

    if args.expiry_check and payload and r is not None and r.status_code == 200:
        probe_expiry_enforcement(
            polaris_url, realm, r.json()["access_token"], payload.get("exp")
        )

    head("SUMMARY -- what to record before designing the Spark test")
    if r is None or err:
        print("  Token endpoint unreachable. Nothing else could be measured.")
    elif r.status_code != 200:
        print(f"  Internal token endpoint returned {r.status_code}.")
        print("  -> Polaris is likely configured for EXTERNAL authentication.")
        print("  -> Re-run with --token-endpoint pointing at Keycloak, --client-id,")
        print("     PROBE_CLIENT_SECRET, and --no-realm-header.")
    elif payload is None:
        print("  Got a token but could not decode it (opaque). Confirm how Polaris")
        print("  validates it (introspection vs. JWKS) before proceeding.")
    else:
        iss = payload.get("iss")
        print(f"  Issuer : {iss}")
        print(f"  Verdict: {classify_issuer(iss, polaris_url)}")
        print("  If INTERNAL and production is Keycloak, local does NOT mirror prod --")
        print(
            "  add a local Keycloak before test 1/2, or accept non-transferable results."
        )
    print()


if __name__ == "__main__":
    main()
