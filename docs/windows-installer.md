# Windows installer

The Windows installer is a runtime adapter for Handoff Guard Core. It does not contain a separate routing policy. Both the executable and the manual-installation document consume `runtime/custom-instructions.txt`, the canonical ChatGPT runtime template.

## User flow

1. Open ChatGPT Desktop.
2. Run `HandoffGuard-Installer-v0.1.0.exe`.
3. Choose **Install / Update**.
4. Review the complete before/after preview.
5. Confirm the change.
6. The installer creates a local backup, writes only the versioned managed block, reads it back, and reports whether verification succeeded.

The installer uses Microsoft UI Automation through `pywinauto` and accessible control names. It does not use absolute screen coordinates, inspect the ChatGPT database, read chats, or access account credentials. If the current ChatGPT build does not expose one uniquely identifiable Custom Instructions editor, automatic installation stops without writing.

## Copy & Open Settings fallback

Choose **Copy & Open Settings** when automatic navigation or reading is unavailable. The installer copies the complete managed block and opens ChatGPT Personalization when possible. Paste the block alongside existing instructions; do not replace unrelated text.

## Backup and recovery

Before a confirmed write, the original Custom Instructions value is stored under:

```text
%LOCALAPPDATA%\HandoffGuard\backups\
```

Backups remain on the device and are never uploaded. A failed read never produces a write. A failed post-save verification reports the exact backup path.

## Build

Install the declared build dependencies, then run:

```powershell
./scripts/build_installer.ps1
```

The release artifacts are `dist/HandoffGuard-Installer-v0.1.0.exe` and its generated `.sha256` file. Publish both with the matching source archive through GitHub Releases.

The local development build is unsigned. A public release should be Authenticode-signed when a trusted code-signing certificate is available; until then, document the unsigned status and publish the generated SHA-256 checksum without implying publisher verification.

## Real-device acceptance

UI Automation selectors can change between ChatGPT Desktop releases. The repository tests verify installer lifecycle behavior through a fake settings adapter, not the live ChatGPT accessibility tree. Before publishing a release, run install, update, repair, uninstall, and fallback acceptance on a disposable Custom Instructions value in the current public ChatGPT Desktop build.
