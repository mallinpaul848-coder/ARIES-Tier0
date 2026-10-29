import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import Arweave from "arweave";
import { TurboFactory } from "@ardrive/turbo-sdk";

const SITE_PATH = "mallin-decentralized/permaweb/mallin-platform.html";
const MAX_FREE_ITEM_BYTES = 105 * 1024;
const site = await readFile(SITE_PATH);

if (site.length === 0 || site.length > MAX_FREE_ITEM_BYTES) {
  throw new Error(`Stopped before upload: page size ${site.length} bytes; free single-item limit is ${MAX_FREE_ITEM_BYTES} bytes.`);
}
const source = site.toString("utf8");
for (const required of [
  "CreateMLCEngine",
  "@mlc-ai/web-llm@0.2.86",
  "SmolLM2-360M-Instruct-q4f32_1-MLC",
  "Llama-3.2-1B-Instruct-q4f32_1-MLC"
]) {
  if (!source.includes(required)) throw new Error(`Stopped before upload: required browser-model content missing: ${required}`);
}

console.log(`Prepared MALLIN standalone HTML: ${site.length} bytes.`);
console.log("No existing user wallet or payment credential will be used.");
console.log("Creating a fresh temporary Arweave signing key for this one permanent public file.");

const arweave = Arweave.init({ host: "arweave.net", port: 443, protocol: "https" });
let jwk = await arweave.wallets.generate();
const turbo = TurboFactory.authenticated({ privateKey: jwk, token: "arweave" });

// Check the wallet's own free-tier allowance before sending the file.
// We do not attach a funding mode, top-up method, or payment credential.
const freeStatus = await turbo.getFreeStatus();
console.log("Free-tier wallet status:", JSON.stringify(freeStatus));
if (typeof freeStatus?.bytesRemaining === "number" && freeStatus.bytesRemaining < site.length) {
  jwk = null;
  throw new Error("Stopped before upload: free wallet allowance is insufficient. No payment was attempted.");
}

const result = await turbo.upload({
  data: site,
  dataItemOpts: {
    tags: [
      { name: "Content-Type", value: "text/html; charset=utf-8" },
      { name: "App-Name", value: "MALLIN-Platform" },
      { name: "Title", value: "MALLIN Platform - ARIES AI" },
      { name: "Website-Version", value: "browser-local-model-webllm-0.2.86" }
    ]
  }
});
jwk = null;

if (!result?.id) throw new Error("Upload returned no permanent transaction ID; publication is unconfirmed.");
if (result.winc !== undefined && BigInt(String(result.winc)) !== 0n) {
  console.log("WARNING: upload receipt reports a non-zero cost:", result.winc);
  throw new Error("Unexpected non-zero upload cost; inspect the receipt and do not run another upload.");
}
console.log("Permanent transaction ID:", result.id);
console.log("Upload receipt:", JSON.stringify(result));

// Retrieve raw bytes and compare them with the original HTML. A newly uploaded item
// may return 404 briefly while indexing. A gateway 404 is retried; other failures stop.
const expectedHash = createHash("sha256").update(site).digest("hex");
let verified = false;
let lastStatus = "not attempted";
for (let attempt = 1; attempt <= 12; attempt++) {
  const response = await fetch(`https://turbo-gateway.com/raw/${encodeURIComponent(result.id)}`);
  lastStatus = String(response.status);
  if (response.status === 200) {
    const retrieved = Buffer.from(await response.arrayBuffer());
    const retrievedHash = createHash("sha256").update(retrieved).digest("hex");
    if (retrievedHash !== expectedHash) throw new Error("Gateway returned bytes with a mismatched SHA-256 hash.");
    verified = true;
    console.log("Verified exact bytes from Turbo gateway; SHA-256:", expectedHash);
    break;
  }
  if (response.status !== 404) throw new Error(`Gateway verification stopped on HTTP ${response.status}.`);
  await new Promise(resolve => setTimeout(resolve, 5000));
}
if (!verified) {
  console.log("Upload receipt has a permanent ID, but gateway indexing did not finish in the verification window.");
  console.log("Do not upload again immediately; retry verification against the same ID later.");
  const summary = [
    "## MALLIN permanent upload — ID issued, indexing pending",
    "",
    `- **Transaction ID:** ${result.id}`,
    `- **File size:** ${site.length} bytes`,
    `- **Expected SHA-256:** ${expectedHash}`,
    `- **Last gateway response:** HTTP ${lastStatus}`,
    `- **Public URL (gateway):** https://turbo-gateway.com/${result.id}`,
    "",
    "The upload service returned an ID, but exact-byte gateway verification is still pending."
  ].join("\n");
  await import("node:fs/promises").then(fs => fs.appendFile(process.env.GITHUB_STEP_SUMMARY, summary + "\n"));
  process.exitCode = 1;
} else {
  const publicUrl = `https://turbo-gateway.com/${result.id}`;
  const alternateUrl = `https://arweave.net/${result.id}`;
  const summary = [
    "## MALLIN permanent upload — bytes verified",
    "",
    `- **Public website:** ${publicUrl}`,
    `- **Alternate gateway:** ${alternateUrl}`,
    `- **Transaction ID:** ${result.id}`,
    `- **Upload cost (winc):** ${result.winc ?? "not reported"}`,
    `- **File size:** ${site.length} bytes`,
    `- **SHA-256:** ${expectedHash}`,
    "- **Model:** browser-local WebLLM; first visit still downloads model/runtime artifacts to each visitor's browser.",
    "",
    "Test the public website in a fresh private/incognito browser window. A verified raw-byte hash proves the stored page matches this file; it does not by itself prove browser WebGPU generation on every device."
  ].join("\n");
  await import("node:fs/promises").then(fs => fs.appendFile(process.env.GITHUB_STEP_SUMMARY, summary + "\n"));
  console.log("PUBLIC URL:", publicUrl);
  console.log("ALTERNATE URL:", alternateUrl);
}
