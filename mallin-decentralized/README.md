# MALLIN Platform — browser-local ARIES chat and permanent publishing

## Browser-local language model

The MALLIN static chat page includes browser-side language-model inference using WebLLM/WebGPU. Visitors can select:

- **SmolLM2 360M Instruct, Q4F32** — compact starter model.
- **Llama 3.2 1B Instruct, Q4F32** — larger starter model.

A normal chat question triggers model loading if it is not already loaded. For genuine model generation, visitors need a secure HTTPS origin, supported WebGPU, enough GPU memory, and an internet connection for first-time runtime/weight downloads. The model answers locally in each visitor's browser; no hosted AI chat API is used by this path. It is not the project's custom ARIES weights and has not been independently certified.

## Publish a permanent public URL

The single-file website export is `permaweb/mallin-platform.html`. It contains the CSS and JavaScript inline and is currently below the documented 105 KiB free per-item upload limit.

A manual GitHub Actions workflow publishes this one file to Arweave and verifies the retrieved bytes:

- Workflow: `.github/workflows/publish-mallin-permaweb.yml`
- Publisher script: `../../scripts/publish_mallin_permaweb.mjs`
- User-facing publishing page: `permaweb/PUBLISH-MALLIN-PERMAWEB.html`

### Run it

1. Open https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/publish-mallin-permaweb.yml while signed in to GitHub.
2. Click **Run workflow**.
3. Choose **yes** in the confirmation input and start the run.
4. Wait for the workflow summary. It should include the permanent transaction ID, public gateway URL, upload cost, file size, and SHA-256 verification result.
5. Open the public URL in a fresh private browser window. Check that the page loads and test model loading on a WebGPU-capable device.

The action generates an ephemeral Arweave signing key in the temporary runner; it does not read an existing user wallet or commit a private key. It checks size/free allowance first, has no payment/top-up code, and stops instead of paying if the free path is unavailable. Arweave publication is immutable/public, so the manual workflow requires an explicit `yes` confirmation. The action uses GitHub Actions only as a one-time publication runner; the served HTML is retrieved from Arweave gateways rather than GitHub or Vercel.

Official upload docs describe a 105 KiB free per-item tier, subject to current wallet and IP-range quotas, with a 10 MiB lifetime limit per wallet. It may fail if the per-IP free allocation is exhausted; the script deliberately does not try a paid fallback:
- https://docs.ar.io/build/upload/upload-and-verify/
- https://docs.ar.io/build/upload/x402-uploading-to-turbo

## Status honesty

The browser inference code passed JavaScript syntax checks and model IDs are listed in the pinned WebLLM model configuration. This does not prove real model generation on every device. The site is not considered publicly launched until the manual workflow succeeds, the returned URL loads from a separate browser, and an actual WebGPU response has been observed.

## Files

- `index.html` — source chat UI
- `styles.css` — cosmic design
- `app.js` — local inference and model-loading logic
- `manifest.webmanifest` / `sw.js` — PWA metadata/static shell cache
- `permaweb/mallin-platform.html` — standalone permanent-site export
- `permaweb/PUBLISH-MALLIN-PERMAWEB.html` — manual publishing instructions
