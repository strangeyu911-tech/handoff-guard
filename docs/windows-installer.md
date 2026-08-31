# Windows Guided Install

The Windows executable is a Guided Install adapter for Handoff Guard Core. It
does not access ChatGPT Desktop settings and does not contain a separate
routing policy. The executable and the manual-installation document consume
`runtime/custom-instructions.txt`, the canonical ChatGPT runtime template.

## User flow

1. Run `HandoffGuard-Installer-v0.1.0.exe`.
2. Choose **Generate block** or paste your own current Custom Instructions and
   choose **Update instructions**, **Removal instructions**, or **Repair
   instructions**.
3. Review the local result and use **Copy managed block** or **Copy generated
   instructions**.
4. Choose **Open ChatGPT Web**. The installer opens only
   `https://chatgpt.com/`.
5. In ChatGPT, open `Settings → Personalization → Custom Instructions`.
6. Preserve all unrelated user content, paste or replace only the Handoff Guard
   managed block, and save manually.

The success state is intentionally local: `Handoff Guard block copied. No
ChatGPT account setting was changed.` The installer cannot verify a paste, save,
or account sync.

## Local text operations

The installer retains deterministic managed-block operations for text supplied
by the user:

- **Generate** creates the canonical versioned block.
- **Update** replaces one valid old block in place and preserves text outside it.
- **Removal** removes only the Handoff Guard block.
- **Repair** removes the damaged Handoff Guard region locally and generates a
  fresh canonical block.
- **Validation** checks the payload, version, markers, and checksum locally.

No operation writes to ChatGPT. A local backup is only possible for text the
user explicitly supplies to the local service; the Guided Install UI does not
claim to back up ChatGPT account settings automatically.

## Why there is no automatic install

ChatGPT does not provide a public Custom Instructions API for the current
product path. In the currently tested ChatGPT Desktop version, the editor did
not expose a reliable supported contract for this operation, and there is no
supported settings deep link. This is a scoped platform conclusion, not a
claim about every future version or plan. The product therefore does not use
UIA selectors, coordinate clicks, OCR, guessed `chatgpt://` links, private
APIs, tokens, cookies, or session data.

## Build

Install the declared build dependencies, then run:

```powershell
./scripts/build_installer.ps1
```

The release artifacts are `dist/HandoffGuard-Installer-v0.1.0.exe` and its
generated `.sha256` file. Publish both with the matching source archive through
GitHub Releases.

The local development build is unsigned. A public release should be
Authenticode-signed when a trusted code-signing certificate is available;
until then, document the unsigned status and publish the generated SHA-256
checksum without implying publisher verification.

## Acceptance

Run the relevant local tests before publishing. Acceptance should confirm that
Generate, Update, Removal, Repair, Copy, and Open ChatGPT Web produce the
expected local result and user guidance. No live ChatGPT account is needed or
modified for this acceptance; final manual save remains a user action.
