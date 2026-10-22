"""Small authoritative DNS server for explicitly configured zones.

This service answers only for configured zones. It is not a recursive resolver.
"""
from __future__ import annotations

import json
import os
import ipaddress
from pathlib import Path
from typing import Any

from dnslib import A, AAAA, CNAME, DNSLabel, DNSRecord, MX, NS, QTYPE, RCODE, RR, SOA, TXT
from dnslib.server import BaseResolver, DNSServer


SUPPORTED = {"A", "AAAA", "CNAME", "MX", "NS", "TXT"}


def canonical(name: str) -> str:
    value = name.strip().lower()
    return value if value.endswith(".") else value + "."


def fqdn(zone: str, owner: str) -> str:
    if owner == "@":
        return canonical(zone)
    if owner.endswith("."):
        return canonical(owner)
    return canonical(owner + "." + zone.rstrip("."))


def load_zones(path: str) -> dict[str, dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("Zone file must be a non-empty JSON object.")
    zones: dict[str, dict[str, Any]] = {}
    for raw_zone, config in data.items():
        zone = canonical(raw_zone)
        if not isinstance(config, dict) or not isinstance(config.get("records"), dict):
            raise ValueError(f"Invalid zone configuration for {zone}")
        config.setdefault("ttl", 300)
        config.setdefault("soa", {})
        zones[zone] = config
    return zones


class AuthoritativeResolver(BaseResolver):
    def __init__(self, zones: dict[str, dict[str, Any]]) -> None:
        self.zones = zones

    def _zone_for(self, qname: str) -> tuple[str, dict[str, Any]] | None:
        matches = [(zone, cfg) for zone, cfg in self.zones.items()
                   if qname == zone or qname.endswith("." + zone)]
        return max(matches, key=lambda item: len(item[0])) if matches else None

    def _record(self, rtype: str, value: str):
        if rtype == "A":
            ipaddress.IPv4Address(value)
            return A(value)
        if rtype == "AAAA":
            ipaddress.IPv6Address(value)
            return AAAA(value)
        if rtype == "CNAME":
            return CNAME(canonical(value))
        if rtype == "NS":
            return NS(canonical(value))
        if rtype == "MX":
            parts = value.split(maxsplit=1)
            if len(parts) != 2:
                raise ValueError("MX values must be '<preference> <hostname>'.")
            return MX(canonical(parts[1]), preference=int(parts[0]))
        if rtype == "TXT":
            return TXT(value)
        raise ValueError(f"Unsupported DNS record type: {rtype}")

    def resolve(self, request: DNSRecord, handler):
        reply = request.reply()
        reply.header.aa = 1
        q = request.q
        qname = canonical(str(q.qname))
        qtype = QTYPE.get(q.qtype)
        match = self._zone_for(qname)
        if match is None:
            reply.header.aa = 0
            reply.header.rcode = RCODE.REFUSED
            return reply

        zone, cfg = match
        soa = cfg.get("soa", {})
        ttl = int(cfg.get("ttl", 300))
        if qtype == "SOA" and qname == zone:
            reply.add_answer(RR(
                rname=DNSLabel(zone), rtype=QTYPE.SOA, ttl=ttl,
                rdata=SOA(
                    mname=canonical(soa.get("mname", "ns1." + zone)),
                    rname=canonical(soa.get("rname", "hostmaster." + zone)),
                    times=(int(soa.get("serial", 1)), int(soa.get("refresh", 3600)),
                           int(soa.get("retry", 600)), int(soa.get("expire", 1209600)),
                           int(soa.get("minimum", ttl)))
                )
            ))
            return reply

        records = cfg["records"]
        owner_records: list[dict[str, str]] | None = None
        for owner, values in records.items():
            if fqdn(zone, owner) == qname:
                owner_records = values
                break
        if owner_records is None:
            reply.header.rcode = RCODE.NXDOMAIN
            return reply

        for item in owner_records:
            rtype = str(item.get("type", "")).upper()
            value = str(item.get("value", ""))
            if rtype not in SUPPORTED:
                continue
            if qtype not in (rtype, "ANY"):
                continue
            reply.add_answer(RR(
                rname=DNSLabel(qname), rtype=QTYPE.get(rtype), ttl=ttl,
                rdata=self._record(rtype, value)
            ))
        if not reply.rr and qtype not in ("ANY",):
            # Name exists, but there is no record of the requested type (NODATA).
            reply.header.rcode = RCODE.NOERROR
        return reply


def main() -> None:
    zone_path = os.getenv("MALLIN_DNS_ZONE_FILE", "foundation/dns/zones.json")
    zones = load_zones(zone_path)
    host = os.getenv("MALLIN_DNS_HOST", "127.0.0.1")
    port = int(os.getenv("MALLIN_DNS_PORT", "8053"))
    resolver = AuthoritativeResolver(zones)
    udp = DNSServer(resolver, port=port, address=host, tcp=False)
    tcp = DNSServer(resolver, port=port, address=host, tcp=True)
    print(f"MALLIN authoritative DNS listening on {host}:{port} UDP/TCP; zones={','.join(zones)}")
    udp.start_thread()
    try:
        tcp.start()
    except KeyboardInterrupt:
        udp.stop()
        tcp.stop()


if __name__ == "__main__":
    main()
