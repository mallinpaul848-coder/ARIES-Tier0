# MALLIN Super Unlocker — portable Windows edition

## What this is

A flash-drive-friendly Windows menu for USB device identification and read-only ADB/Fastboot connection checks, with direct links to official owner-authorized service paths. It applies the PRISE idea as a transparent triage framework:

- **P — Priority:** What does the owner need to resolve?
- **R — Risk:** Could this action erase data or affect device security/warranty?
- **I — Impact:** Which capability is affected?
- **S — System constraint:** Is release controlled by an account owner, carrier, OEM, or organization?
- **E — Evidence:** What do the device state and official documentation actually support?

This is a decision/triage aid, not a mathematical proof of universal unlocking.

## Put it on a flash drive

1. Download the files in this folder to a Windows PC.
2. Keep `START-MALLIN.cmd` and `MALLIN-Super-Unlocker.ps1` in the same folder on the USB drive.
3. Double-click `START-MALLIN.cmd`.
4. Use menu option 1 to scan the Windows USB device inventory. For Android ADB/Fastboot detection, see the optional setup below.
5. Select the relevant official service path from the menu.

The portable script uses Windows PowerShell built into supported Windows systems. Some Windows environments may restrict script execution by policy.

## Optional Android ADB/Fastboot detection

The toolkit does not redistribute Android Platform-Tools. Download the current official Google SDK Platform-Tools ZIP from:

https://developer.android.com/tools/releases/platform-tools

Extract it so the USB drive has this layout:

```text
USB drive
└── portable-super-unlocker
    ├── START-MALLIN.cmd
    ├── MALLIN-Super-Unlocker.ps1
    └── platform-tools
        ├── adb.exe
        ├── fastboot.exe
        └── (official supporting files)
```

Then use menu option 2 or 3. ADB will only see devices that already have USB debugging enabled and have authorized the connected PC. A device in Fastboot must be put there using the manufacturer's supported procedure.

## What it cannot do

This is **not** a universal unlocker. It does not remove phone screen locks, bypass Apple Activation Lock, defeat Android Google Factory Reset Protection (FRP), release MDM enrollment, bypass carrier eligibility, extract data, or run exploit code. Those mechanisms are designed to require the linked account, carrier, organization, or manufacturer authorization. Do not trust software promising a universal one-click bypass.

The program does not send commands to erase, unlock, flash, or relock a device. It uses only USB inventory checks, `adb devices`, and `fastboot devices` for diagnostics. Owner-authorized bootloader unlocking, where a manufacturer supports it, is a separate OEM-controlled action. It can void warranty or affect device security, requires physical interaction, and normally factory-resets the phone. Follow the device maker's exact instructions.

## Official reference links

- Apple forgotten passcode with a computer: https://support.apple.com/118430
- Apple Activation Lock: https://support.apple.com/108934
- Google Account recovery / FRP account recovery: https://support.google.com/accounts/answer/7682439
- Android SDK Platform-Tools: https://developer.android.com/tools/releases/platform-tools
- Android bootloader locking/unlocking: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
- FCC carrier unlocking guide: https://www.fcc.gov/consumers/guides/cell-phone-unlocking

Independent utility; not affiliated with Apple, Google, Samsung, or mobile carriers. A read-only USB inventory entry does not prove device ownership or compatibility.