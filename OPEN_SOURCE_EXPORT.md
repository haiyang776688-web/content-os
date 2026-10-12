# Open-source export note

The original development repository is intentionally kept private because its history contains private experimental media, including a local cloned-voice sample and binary validation artifacts.

The `open-source-prep` branch is a **sanitized snapshot candidate**, not a guarantee that the private repository history is safe to expose.

Recommended publication process:

1. Export the working tree of `open-source-prep` without `.git` history.
2. Create a new public repository.
3. Commit the exported files as a fresh initial commit.
4. Keep the original development repository private as an archive.

Do **not** simply switch the original repository from Private to Public.
