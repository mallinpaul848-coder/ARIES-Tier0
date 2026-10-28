# MALLIN Super Unlocker — portable, read-only device triage for Windows
# This tool never removes passcodes, bypasses account locks, erases data, or flashes firmware.
$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PlatformDirs = @(
    (Join-Path $Root "platform-tools"),
    (Join-Path $Root "android-platform-tools"),
    $Root
)
$Adb = $null
$Fastboot = $null
foreach ($dir in $PlatformDirs) {
    if (-not $Adb -and (Test-Path (Join-Path $dir "adb.exe"))) { $Adb = Join-Path $dir "adb.exe" }
    if (-not $Fastboot -and (Test-Path (Join-Path $dir "fastboot.exe"))) { $Fastboot = Join-Path $dir "fastboot.exe" }
}
function Header {
    Clear-Host
    Write-Host ""
    Write-Host "  MALLIN SUPER UNLOCKER" -ForegroundColor Magenta
    Write-Host "  PRISE device triage | Windows portable edition" -ForegroundColor DarkGray
    Write-Host "  ------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  P  Priority  | R  Risk  | I  Impact" -ForegroundColor Gray
    Write-Host "  S  System constraint | E  Evidence" -ForegroundColor Gray
    Write-Host ""
}
function Pause-Tool { Write-Host ""; Read-Host "Press Enter to return to the menu" | Out-Null }
function Open-Official([string]$Url) {
    try { Start-Process $Url; Write-Host "Opened official support page in your browser." -ForegroundColor Green }
    catch { Write-Host "Could not open the browser. Open this link manually: $Url" -ForegroundColor Yellow }
}
function Scan-Usb {
    Header
    Write-Host "PRISE: identify the device and its state before choosing an action." -ForegroundColor Cyan
    Write-Host ""
    try {
        $items = Get-CimInstance Win32_PnPEntity | Where-Object {
            $_.Name -match '(?i)iphone|ipad|apple mobile|android|samsung|pixel|xiaomi|huawei|oneplus|motorola|adb interface|fastboot|mtp usb|portable device'
        } | Select-Object -First 30 Name, Status
        if ($items) {
            foreach ($item in $items) {
                $status = if ($item.Status) { $item.Status } else { "Status unavailable" }
                Write-Host ("  [{0}] {1}" -f $status, $item.Name)
            }
        } else {
            Write-Host "  No recognizable phone/tablet entry found in Windows device inventory." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Windows device inventory could not be queried." -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Privacy: this scan does not display IMEI, serial numbers, photos, or personal files." -ForegroundColor DarkGray
    Write-Host "A phone may appear as Unknown device until its official USB driver is installed."
    Pause-Tool
}
function Check-Adb {
    Header
    Write-Host "PRISE check: ADB works only when Android USB debugging is already enabled and this PC is authorized." -ForegroundColor Cyan
    if (-not $Adb) {
        Write-Host ""
        Write-Host "ADB is not bundled with this toolkit." -ForegroundColor Yellow
        Write-Host "Download Google's official SDK Platform-Tools ZIP, extract it, and place its platform-tools folder beside this script."
        Write-Host "Official download: https://developer.android.com/tools/releases/platform-tools"
        Pause-Tool
        return
    }
    Write-Host ""
    $raw = @(& $Adb devices 2>&1 | ForEach-Object { "$_" })
    $rows = @($raw | Where-Object { $_ -match '^\S+\s+(device|unauthorized|offline)$' })
    if (-not $rows) {
        Write-Host "No ADB-authorized device detected. Unlock the phone normally and accept its 'Allow USB debugging' prompt if available." -ForegroundColor Yellow
        Write-Host "This utility does not enable debugging or bypass the phone's screen lock."
    } else {
        foreach ($row in $rows) {
            if ($row -match '\s+device$') {
                Write-Host "Android connected and ADB-authorized." -ForegroundColor Green
            } elseif ($row -match '\s+unauthorized$') {
                Write-Host "Android detected but this PC is not authorized. Approve the on-phone prompt if you can access it." -ForegroundColor Yellow
            } elseif ($row -match '\s+offline$') {
                Write-Host "Android ADB connection is offline. Try another cable/USB port and reconnect." -ForegroundColor Yellow
            }
        }
    }
    Write-Host ""
    Write-Host "Read-only check only. No commands are sent to change device settings or files." -ForegroundColor DarkGray
    Pause-Tool
}
function Check-Fastboot {
    Header
    Write-Host "PRISE check: detect a phone already in fastboot/bootloader mode." -ForegroundColor Cyan
    if (-not $Fastboot) {
        Write-Host ""
        Write-Host "Fastboot is not bundled with this toolkit." -ForegroundColor Yellow
        Write-Host "Download Google's official SDK Platform-Tools ZIP and place its platform-tools folder beside this script."
        Write-Host "Official download: https://developer.android.com/tools/releases/platform-tools"
        Pause-Tool
        return
    }
    Write-Host ""
    $raw = @(& $Fastboot devices 2>&1 | ForEach-Object { "$_" })
    $rows = @($raw | Where-Object { $_ -match '^\S+\s+fastboot\b' })
    if ($rows.Count -gt 0) {
        Write-Host "Fastboot device detected ($($rows.Count))." -ForegroundColor Green
        Write-Host "The toolkit deliberately does not issue unlock, erase, flash, or relock commands."
        Write-Host "On supported Android devices, bootloader unlocking is an OEM-controlled action, requires physical confirmation, and normally erases all user data."
        Write-Host "Read the Android Open Source Project guidance before proceeding:"
        Write-Host "https://source.android.com/docs/core/architecture/bootloader/locking_unlocking" -ForegroundColor Cyan
    } else {
        Write-Host "No fastboot device detected." -ForegroundColor Yellow
        Write-Host "Many phones enter bootloader mode only with a model-specific button combination. Consult the device maker's official instructions."
    }
    Pause-Tool
}
function Show-PRISE {
    Header
    Write-Host "PRISE is used here as a transparent TRIAGE framework, not a claim of universal unlocking." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "P — Priority: identify the immediate goal (screen access, setup lock, SIM lock, or bootloader)."
    Write-Host "R — Risk: mark data erasure, warranty, and security risks before taking action."
    Write-Host "I — Impact: distinguish a forgotten screen passcode from an account/anti-theft lock."
    Write-Host "S — System constraint: account owner, carrier, device maker, or organization controls the release."
    Write-Host "E — Evidence: choose a method supported by the detected device state and official documentation."
    Write-Host ""
    Write-Host "Triage rule: detect first; do only read-only diagnostics automatically; require the owner to use the authorized provider for state-changing operations."
    Pause-Tool
}
function Show-Menu {
    Header
    Write-Host "  1  Scan connected USB phone/tablet (read-only)"
    Write-Host "  2  Check Android ADB connection/authorization"
    Write-Host "  3  Check Android Fastboot connection"
    Write-Host "  4  iPhone forgotten passcode — official computer restore"
    Write-Host "  5  iPhone Activation Lock — official ownership/account route"
    Write-Host "  6  Android Google FRP — official account recovery"
    Write-Host "  7  Carrier/SIM lock — request unlock from carrier"
    Write-Host "  8  Supported Android bootloader — official OEM-controlled process"
    Write-Host "  9  Explain PRISE triage"
    Write-Host "  0  Exit"
    Write-Host ""
    Write-Host "  No auto-unlock, account bypass, data extraction, erase, or firmware flashing." -ForegroundColor Yellow
}
while ($true) {
    Show-Menu
    $choice = Read-Host "Choose an option"
    switch ($choice) {
        "1" { Scan-Usb }
        "2" { Check-Adb }
        "3" { Check-Fastboot }
        "4" { Open-Official "https://support.apple.com/118430"; Pause-Tool }
        "5" { Open-Official "https://support.apple.com/108934"; Pause-Tool }
        "6" { Open-Official "https://support.google.com/accounts/answer/7682439"; Pause-Tool }
        "7" { Open-Official "https://www.fcc.gov/consumers/guides/cell-phone-unlocking"; Pause-Tool }
        "8" { Open-Official "https://source.android.com/docs/core/architecture/bootloader/locking_unlocking"; Pause-Tool }
        "9" { Show-PRISE }
        "0" { break }
        default { Write-Host "Choose a number from 0 to 9." -ForegroundColor Yellow; Start-Sleep -Seconds 1 }
    }
}
