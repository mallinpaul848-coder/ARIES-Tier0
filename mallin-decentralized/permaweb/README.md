# MALLIN Permaweb upload

This is the single-file MALLIN front-end export. CSS and JavaScript are embedded, so the HTML has no local sibling-file requirements.

## Publish once to decentralized permanent storage

1. Download `mallin-platform.html` to your computer.
2. Open the official ArDrive application: https://app.ardrive.io/
3. Connect a wallet only within the official website. Never paste private keys into ChatGPT or into the HTML file.
4. Upload `mallin-platform.html) as a **public** file. Do not publish secrets or private information; published content is permanent and public.
5. Review the displayed cost before approving. Current official ar.io docs state that mainnet uploads up to 105 KiB per item may fall within a free tier, limited by remaining lifetime allowance per wallet. This file is below 105 KiB, but free eligibility depends on current allowance/rules: https://docs.ar.io/build/upload/upload-and-verify/
6. When the upload confirms, use the public preview / transaction URL from the app. Open in a private browser window, then share that URL.

## Why this avoids your device as a server

The file is stored on Arweave's decentralized permanent storage network. Your personal phone and home internet do not need to stay online as the server. The transaction ID is a permanent content identifier; normal browser viewing usually uses a gateway. The storage does not depend solely on ArDrive remaining available, but gateways and the public internet are still infrastructure operated by the network ecosystem. Sources: https://ardrive.io/ and https://docs.ar.io/learn/gateways

## Limits

- Permanent uploads are immutable. Publishing personal data, API keys, secrets, or copyrighted content without permission may be impossible to undo.
- This static MALLIN page is not a bundled language model. It currently offers a demo interface and optional compatible-model endpoint field; it will not generate full ARIES answers unless a model backend exists.
- The website URL will not be known until the upload succeeds. This repository does not claim the site has been published.
