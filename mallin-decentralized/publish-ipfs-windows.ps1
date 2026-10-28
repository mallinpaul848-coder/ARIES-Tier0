# Publish the MALLIN static front end into the LOCAL IPFS node (Kubo).
# No hosted pinning service or public gateway is used by this script.
$ErrorActionPreference = "Stop"
try {
    $ipfsCommand = Get-Command ipfs -ErrorAction Stop
} catch {
    Write-Host "IPFS Kubo CLI is not installed or ipfs.exe is not on PATH." -ForegroundColor Yellow
    Write-Host "Install the official Kubo CLI: https://docs.ipfs.tech/install/command-line/"
    exit 1
}
$siteRoot = $PSScriptRoot
Write-Host "MALLIN Platform — IPFS local publish" -ForegroundColor Magenta
Write-Host "Site folder: $siteRoot"
try {
    $version = & ipfs --version
    Write-Host $version
    $idOutput = & ipfs id 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Your local IPFS node is not available. Open another PowerShell terminal, run 'ipfs daemon', and try again." -ForegroundColor Yellow
        exit 2
    }
} catch {
    Write-Host "Could not contact the local IPFS node. Start it with 'ipfs daemon' and retry." -ForegroundColor Yellow
    exit 2
}
Write-Host ""
Write-Host "Adding website files to your LOCAL IPFS node..." -ForegroundColor Cyan
$cid = (& ipfs add -Qr "$siteRoot" 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $cid -notmatch '^(Qm[1-9A-HJ-NP-Za-km-z]{44}|bafy[a-z2-7]+)$') {
    Write-Host "IPFS did not return a recognizable content identifier. Command output:" -ForegroundColor Red
    Write-Host $cid
    exit 3
}
Write-Host ""
Write-Host "PUBLISH COMPLETE TO YOUR LOCAL IPFS NODE" -ForegroundColor Green
Write-Host "CID: $cid"
Write-Host "IPFS URI (for IPFS-capable clients): ipfs://$cid/"
Write-Host "Local test URL (same machine only): http://127.0.0.1:8080/ipfs/$cid/"
Write-Host ""
Write-Host "This is not a guaranteed public HTTPS link. Your IPFS node must stay online and reachable." -ForegroundColor Yellow
Write-Host "A standard browser without IPFS support would require a gateway, which would be a third-party dependency."
Write-Host "For genuine AI responses, separately run an inference server you control; the static page is a front-end only."
