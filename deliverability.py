"""
Decide whether a prospect's mail server can plausibly receive a message.

Why
---
The first two businesses this system emailed both hard-bounced. Not "user
unknown" — their mail servers refused connections outright:

    [ashevillepressurewashing.com 3.33.130.190: timed out]

Every one of those sends consumed an approval decision from Tom, a slot in the
daily send limit, and a proposal draft, for a message that could never arrive.
Checking first is cheap; approving a dead address is not.

What this does and does not prove
---------------------------------
Two signals, deliberately treated differently because their reliability differs:

  * **No MX records at all** is a hard, stable fact about a domain. Mail cannot
    be delivered. Safe to act on.
  * **MX exists but will not accept a connection** is a snapshot. A server can be
    briefly down, rate-limiting, or blocking cloud IP ranges. Worth warning a
    human about; not worth silently dropping a real prospect over.

Neither proves a specific mailbox exists. This never sends mail and never
attempts a RCPT probe, which annoys mail administrators and gets senders
blocklisted.
"""

import socket

DEFAULT_TIMEOUT = 5
SMTP_PORT = 25

DELIVERABLE = "deliverable"
NO_MX = "no_mx"
UNREACHABLE = "unreachable"
UNKNOWN = "unknown"

_cache = {}


def _mx_hosts(domain, timeout=DEFAULT_TIMEOUT):
    """
    Mail exchangers for a domain, best preference first.

    Returns None (not an empty list) when the lookup itself could not be
    performed, so "we could not check" stays distinct from "there are none".
    """
    try:
        import dns.resolver
    except ImportError:
        return None

    resolver = dns.resolver.Resolver()
    resolver.lifetime = timeout
    resolver.timeout = timeout
    try:
        answers = resolver.resolve(domain, "MX")
    except Exception as exc:
        name = type(exc).__name__
        # NXDOMAIN and NoAnswer are real answers: this domain has no mail route.
        if name in {"NXDOMAIN", "NoAnswer", "NoNameservers"}:
            return []
        return None

    hosts = []
    for record in sorted(answers, key=lambda r: r.preference):
        exchange = str(record.exchange).rstrip(".")
        # RFC 7505 "null MX": a single record of "." is an explicit declaration
        # that the domain accepts no mail at all. Stripping the dot leaves an
        # empty host, which would otherwise be probed as if it were a real
        # server and misreported as merely unreachable.
        if not exchange:
            return []
        hosts.append(exchange)
    return hosts


def _accepts_connection(host, timeout=DEFAULT_TIMEOUT):
    try:
        with socket.create_connection((host, SMTP_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def check_domain(domain, timeout=DEFAULT_TIMEOUT, probe_connection=True, use_cache=True):
    """
    Return {status, reason, mx} for a domain.

    status is one of: deliverable, no_mx, unreachable, unknown.
    Only `no_mx` is treated as a hard stop by callers.
    """
    domain = (domain or "").strip().lower()
    if not domain:
        return {"status": UNKNOWN, "reason": "no domain given", "mx": []}
    if use_cache and domain in _cache:
        return _cache[domain]

    hosts = _mx_hosts(domain, timeout=timeout)
    if hosts is None:
        result = {"status": UNKNOWN,
                  "reason": "MX lookup unavailable (dnspython missing or DNS failed)",
                  "mx": []}
    elif not hosts:
        result = {"status": NO_MX,
                  "reason": "domain publishes no usable MX record (none, or a null MX); "
                            "mail cannot be delivered",
                  "mx": []}
    elif not probe_connection:
        result = {"status": DELIVERABLE, "reason": f"MX present ({hosts[0]})", "mx": hosts}
    elif any(_accepts_connection(host, timeout=timeout) for host in hosts[:2]):
        result = {"status": DELIVERABLE, "reason": f"MX accepted a connection ({hosts[0]})",
                  "mx": hosts}
    else:
        result = {"status": UNREACHABLE,
                  "reason": f"MX exists ({hosts[0]}) but refused a connection on port {SMTP_PORT}",
                  "mx": hosts}

    if use_cache:
        _cache[domain] = result
    return result


def domain_of(address):
    return (address or "").strip().lower().rpartition("@")[2]


def screen(address, **kwargs):
    """Convenience wrapper: check the domain behind an email address."""
    return check_domain(domain_of(address), **kwargs)


def is_hard_fail(result):
    """Only a missing MX is certain enough to drop a prospect over."""
    return result.get("status") == NO_MX


def warning_for(result):
    """A short note for the approval row, or '' when there is nothing to say."""
    status = result.get("status")
    if status == UNREACHABLE:
        return f"DELIVERABILITY WARNING: {result['reason']}. This message may bounce."
    if status == UNKNOWN:
        return f"Deliverability not verified: {result['reason']}."
    return ""
