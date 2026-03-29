"""URL validation to prevent SSRF attacks.

Validates webhook destination URLs against a denylist of private/internal IP ranges
and cloud metadata endpoints. Resolves DNS before making requests and checks the
resolved IP address.
"""

import ipaddress
import socket
from urllib.parse import urlparse


# Private and reserved IP networks that must be blocked
_BLOCKED_NETWORKS = [
    # IPv4 private ranges
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    # IPv4 loopback
    ipaddress.IPv4Network("127.0.0.0/8"),
    # IPv4 link-local
    ipaddress.IPv4Network("169.254.0.0/16"),
    # IPv4 reserved/special
    ipaddress.IPv4Network("0.0.0.0/8"),
    ipaddress.IPv4Network("100.64.0.0/10"),   # Carrier-grade NAT
    ipaddress.IPv4Network("192.0.0.0/24"),     # IETF protocol assignments
    ipaddress.IPv4Network("192.0.2.0/24"),     # TEST-NET-1
    ipaddress.IPv4Network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.IPv4Network("203.0.113.0/24"),   # TEST-NET-3
    ipaddress.IPv4Network("224.0.0.0/4"),      # Multicast
    ipaddress.IPv4Network("240.0.0.0/4"),      # Reserved
    ipaddress.IPv4Network("255.255.255.255/32"),
    # IPv6 private/reserved ranges
    ipaddress.IPv6Network("::1/128"),          # Loopback
    ipaddress.IPv6Network("fc00::/7"),         # Unique local
    ipaddress.IPv6Network("fe80::/10"),        # Link-local
    ipaddress.IPv6Network("::/128"),           # Unspecified
    ipaddress.IPv6Network("::ffff:0:0/96"),    # IPv4-mapped IPv6
]

# Specific blocked hostnames (cloud metadata endpoints)
_BLOCKED_HOSTNAMES = frozenset({
    "metadata.google.internal",
    "metadata.goog",
})

# Allowed URL schemes
_ALLOWED_SCHEMES = frozenset({"http", "https"})


class SSRFError(Exception):
    """Raised when a URL fails SSRF validation."""
    pass


def _is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP address falls within any blocked network range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        # If we cannot parse it, block it to be safe
        return True

    for network in _BLOCKED_NETWORKS:
        if addr in network:
            return True
    return False


def validate_webhook_url(url: str) -> str:
    """Validate a webhook URL is safe to connect to.

    Performs the following checks:
    1. Scheme must be http or https
    2. Hostname must not be empty
    3. Hostname must not be a blocked cloud metadata endpoint
    4. If hostname is a literal IP, it must not be in a private/reserved range
    5. DNS resolution of hostname must not resolve to a private/reserved IP

    Args:
        url: The webhook URL to validate.

    Returns:
        The validated URL string.

    Raises:
        SSRFError: If the URL fails validation.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise SSRFError("Invalid URL format")

    # Check scheme
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise SSRFError(
            f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted."
        )

    # Check hostname exists
    hostname = parsed.hostname
    if not hostname:
        raise SSRFError("URL must contain a valid hostname")

    # Block cloud metadata hostnames
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise SSRFError(f"Hostname '{hostname}' is blocked (cloud metadata endpoint)")

    # Check if hostname is a literal IP address
    try:
        ip_addr = ipaddress.ip_address(hostname)
        if _is_ip_blocked(str(ip_addr)):
            raise SSRFError(
                f"IP address '{hostname}' is in a private/reserved range and cannot be used as a webhook destination"
            )
        # Literal IP passed validation
        return url
    except ValueError:
        # Not a literal IP, continue to DNS resolution
        pass

    # Resolve DNS and check all resolved IPs
    try:
        addr_infos = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise SSRFError(f"Cannot resolve hostname '{hostname}'")

    if not addr_infos:
        raise SSRFError(f"Hostname '{hostname}' did not resolve to any addresses")

    for addr_info in addr_infos:
        ip_str = addr_info[4][0]
        if _is_ip_blocked(ip_str):
            raise SSRFError(
                f"Hostname '{hostname}' resolves to private/reserved IP '{ip_str}' "
                "and cannot be used as a webhook destination"
            )

    return url
