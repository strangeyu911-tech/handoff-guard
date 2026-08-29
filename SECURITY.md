# Security

Handoff Guard's Windows installer modifies ChatGPT Custom Instructions only after displaying a preview and receiving explicit confirmation.

- Existing content is read only to create the preview and preserve it during the edit.
- The original value is backed up locally before every write.
- Custom Instructions, chat history, account tokens, and passwords are never uploaded or requested.
- The installer does not modify ChatGPT databases or credentials.
- Automatic installation stops when the existing value cannot be read or the editor cannot be identified uniquely.
- Uninstall removes only the checksummed Handoff Guard managed block.

Please report security issues privately to the repository owner rather than opening a public issue containing personal Custom Instructions.
