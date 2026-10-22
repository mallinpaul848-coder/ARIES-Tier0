# MALLIN Platform Foundation

This directory is the deployable foundation for the MALLIN AI platform: a static chat client, a provider-neutral HTTP gateway contract, and an authoritative DNS server that you can operate on infrastructure you control.

## Components

- `web/`: standalone responsive chat interface with a purple nebula-style background.
- `dns/`: authoritative DNS service for zones you administer, served over UDP and TCP.
- `deploy/`: container and example zone configuration.
- `tests/`: deterministic DNS protocol tests.

## DNS: what this provides

The DNS server is software you can run yourself. It serves configured authoritative records and does not forward queries to a third-party recursive resolver. It supports A, AAAA, CNAME, TXT, MX, NS, SOA, and basic negative answers.

**Public DNS requires delegation.** A registrar or existing parent-zone operator must delegate your registered domain to reachable authoritative nameservers. This repository cannot create a registered domain, assign a public static IP, open port 53 at a hosting provider, or change parent-zone delegation by itself. Run the DNS container on a host that permits inbound UDP and TCP port 53, configure real records and nameserver addresses, then set the delegation at your registrar. Do not publish the example zone as if you own it.

## Run the DNS server locally

Python 3.12+ is recommended.

```sh
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r foundation/dns/requirements.txt
python foundation/dns/server.py
```

By default, it listens on UDP and TCP port 8053 for local testing. Set `MALLIN_DNS_HOST=0.0.0.0` and `MALLIN_DNS_PORT=53` only on a host where you have permission to bind port 53 and have configured firewall rules. Set `MALLIN_DNS_ZONE_FILE` to the JSON zone file you control.

## Run tests

```sh
pip install -r foundation/dns/requirements.txt pytest
pytest -q foundation/tests
```

## Run the chat interface

Open `foundation/web/index.html` in a browser. It calls the existing ARIES-compatible public API by default. To change the API endpoint, set `window.MALLIN_API_BASE` before the application script runs or edit the default in the HTML. A reachable chat API and a configured model runtime are still required for general-purpose generated answers.

## Security and operations

- Keep provider credentials on the server; never put secret keys in browser JavaScript.
- Do not expose a DNS administration API publicly. Zone edits are made through the controlled zone file and deployment process.
- Use a dedicated non-root service account, firewall rules, backups, monitoring, and a static public IP for production DNS.
- This is a foundation, not a claim that independent hosting, public DNS delegation, domain ownership, or production deployment has already been completed.
