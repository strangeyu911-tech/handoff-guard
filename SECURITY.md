# Security and privacy

Handoff Guard Guided Install generates and validates a managed text block. It
does not read or change ChatGPT account settings.

The only URL it opens is the public ChatGPT Web entry point:
`https://chatgpt.com/`.

- The installer does not access ChatGPT credentials, tokens, cookies, chat
  history, or a local ChatGPT database.
- It does not use UI Automation, coordinate automation, OCR, private APIs, or
  guessed `chatgpt://` deep links.
- It does not send your Custom Instructions to Handoff Guard's servers or
  third parties.
- Local transformations operate only on text you explicitly paste into the
  installer or service.
- Any local backup is user-provided text stored on the device; it is not an
  automatic backup of ChatGPT Custom Instructions.
- Local validation covers the canonical payload, managed-block format, version,
  and checksum. It cannot verify that ChatGPT received, saved, or synchronized
  the block.

When you manually save the generated block in ChatGPT, that content is handled
and synchronized according to [OpenAI's ChatGPT data practices](https://openai.com/policies/how-your-data-is-used-to-improve-model-performance/).

Please report security issues privately to the repository owner rather than
opening a public issue containing personal Custom Instructions.
