import json

from dnslib import DNSRecord, QTYPE, RCODE

from foundation.dns.server import AuthoritativeResolver, load_zones


def resolver(tmp_path):
    zone_file = tmp_path / "zones.json"
    zone_file.write_text(json.dumps({
        "mallin.test.": {
            "ttl": 60,
            "soa": {"mname": "ns1.mallin.test.", "rname": "hostmaster.mallin.test.", "serial": 7},
            "records": {
                "@": [{"type": "A", "value": "192.0.2.10"}, {"type": "NS", "value": "ns1.mallin.test."}],
                "ns1": [{"type": "A", "value": "192.0.2.53"}],
                "www": [{"type": "CNAME", "value": "mallin.test."}],
                "text": [{"type": "TXT", "value": "owned-zone"}]
            }
        }
    }), encoding="utf-8")
    return AuthoritativeResolver(load_zones(str(zone_file)))


def query(r, name, qtype):
    request = DNSRecord.question(name, qtype)
    return r.resolve(request, None)


def test_a_record():
    response = query(resolver_dummy, "mallin.test", "A")
    assert response.header.rcode == RCODE.NOERROR
    assert str(response.rr[0].rdata) == "192.0.2.10"


def test_zone_apex_soa(tmp_path):
    response = query(resolver(tmp_path), "mallin.test", "SOA")
    assert response.header.aa == 1
    assert response.rr[0].rtype == QTYPE.SOA


def test_cname_record(tmp_path):
    response = query(resolver(tmp_path), "www.mallin.test", "CNAME")
    assert response.rr and str(response.rr[0].rdata) == "mallin.test."


def test_unknown_name_is_nxdomain(tmp_path):
    response = query(resolver(tmp_path), "missing.mallin.test", "A")
    assert response.header.rcode == RCODE.NXDOMAIN


def test_outside_zone_is_refused(tmp_path):
    response = query(resolver(tmp_path), "example.org", "A")
    assert response.header.rcode == RCODE.REFUSED


def test_txt_record(tmp_path):
    response = query(resolver(tmp_path), "text.mallin.test", "TXT")
    assert response.rr and "owned-zone" in str(response.rr[0].rdata)


# Shared fixture initialized after helper definitions.
import pytest


@pytest.fixture(autouse=True)
def _set_dummy_resolver(tmp_path, monkeypatch):
    global resolver_dummy
    resolver_dummy = resolver(tmp_path)
