# MALLIN Platform — peer-to-peer IPFS option (no traditional web host)

This folder documents an alternative to Vercel/Render/Netlify: distribute the static MALLIN website over IPFS using an IPFS node you control.

## What this solves / what it does not

- Avoids deploying the site to a conventional website-hosting company.
- Publishes the static front-end files under an IPFS content identifier (CID).
- Provides a local IPFS URL that you can test through your own node.
- Does **not** create a guaranteed permanent public service by itself.
- Does **not** bundle the ARIES language model or create an inference backend.
- Does **not** provide a normal browser HTTPS domain without a gateway/domain setup.
- Does **not** eliminate the need for an IPFS node or other peers to keep the content available.

For no-third-party-hosting use, your own IPFS node must remain available so peers can fetch the site. IPFS is peer-to-peer; it is not a magic upload destination where files stay online forever after all nodes shut down. The IPFS documentation describes public gateways as best-effort utilities, not a production hosting dependency: https://docs.ipfs.tech/concepts/public-utilities/

## Windows setup

1. Install the official IPFS Kubo distribution from https://docs.ipfs.tech/install/command-line/
2. Open PowerShell and verify `ipfs --version`.
3. Start the local node in one terminal with `ipfs daemon`. Leave this terminal running while you publish and test.
4. In another PowerShell terminal, change directory to the repository's `mallin-decentralized` folder.
5. Run `powershell -ExecutionPolicy Bypass -File .\publish-ipfs-windows.ps1`.
6. Save the CID printed by the script. The site content is now added and pinned in this local IPFS node.
7. Open the printed `http://127.0.0.1:8080/ipfs/CID/` URL on that same computer to test it.

## Peer-to-peer access without a public gateway

Share the printed `ipfs://CID/` URI with visitors who have an IPFS-capable browser/client or their own IPFS node. Browser support varies. If visitors use ordinary browsers without IPFS support, they need an HTTP gateway; using a public gateway introduces a third-party dependency. You asked not to use that, so this guide does not rely on one.

The node publishing this content must remain online and reachable for the strongest availability. If it turns off and no other peer has a copy, the content may become unavailable. For updating the site, rerun the script after editing; the new content will have a new CID. IPNS can provide a mutable name but depends on publishing/resolution configuration and an online publisher or another managed route.

## One-time PC vs permanent availability

The PC can be used for a one-time publish, but if you turn it off, this does not guarantee the site will remain available. Since you do not want your personal PC to be the always-on server, an always-on device you own/control would need to run the IPFS node. Without your own always-on node or an outside peer/gateway/pinner, there is no honest way to promise permanent public availability.

## Model limitation

MALLIN's current `app.js` explicitly reports demo mode until a compatible model endpoint you control is configured. IPFS only distributes static files; it does not run model inference. A real AI chat backend must run separately on compute you control if you also want no third-party AI API.

## Official links

- Kubo command-line installation: https://docs.ipfs.tech/install/command-line/
- IPFS public utilities and gateway limitations: https://docs.ipfs.tech/concepts/public-utilities/
- IPFS gateway concepts: https://docs.ipfs.tech/concepts/ipfs-gateway/
- Self-hosted IPFS overview: https://docs.ipfs.tech/how-to/replace-public-gateways-with-self-hosted-ipfs/
