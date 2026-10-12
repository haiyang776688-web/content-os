# Open Source Security Audit

Audit date: 2026-10-12  
Candidate: sanitized working-tree snapshot derived from private `p0/motion-design-contract-1` through `open-source-prep`  
Publication rule: **fresh Git history only**

## Executive result

The original repository history is **not safe to publish** because it previously contained private voice media/configuration, experimental audio/video, cached font binaries and a real Provider verification record. The private repository must remain private.

The candidate working tree can proceed to publication only as an exported snapshot after the checks in this document pass again in the fresh repository and clean clone.

## Scope and methods

The audit examined tracked working-tree content rather than trusting file extensions or the earlier open-source summary. Checks included:

- Git worktrees, local branches, uncommitted paths and branch divergence;
- tracked and untracked file inventory;
- content pattern scans for API keys, GitHub tokens, bearer headers, passwords, private keys, cookies, credentials and common cloud keys;
- email/user identity and absolute local path scan;
- audio/video/font/model/archive and large-file inventory;
- `.env`, `.gitignore`, `.gitmodules`, GitHub Actions, symlinks, submodules and Git LFS;
- Provider/voice registries, Markdown, JSON, Python, JavaScript, fixtures and experiment evidence;
- license/redistribution review of XIAO-Y and historical screenshots;
- clean dependency installation, Python tests, TypeScript and Node dependency audit.

Secret values were never printed into the report.

## High-risk findings and remediation

### 1. Private history

**Finding:** prior commits include a real local cloned-voice profile/reference material, experimental media, cached font copy and Provider live-verification artifact.

**Action:** never change the original repository to Public; never fork it into the public repository; export only the audited tree and initialize a new `.git` directory.

**Status:** publication safeguard required and enforced by release process.

### 2. Real local voice configuration

**Finding:** `YU_LOCAL_V1` described a real local reference voice and the old test hard-coded its ID.

**Action:** remove it from the public tree. Add metadata-only `REFERENCE_VOICE_EXAMPLE_V1` with `PENDING` consent, `UNAVAILABLE` status and no media/path; update the contract test to use the synthetic example.

**Status:** remediated.

### 3. Provider verification snapshot

**Finding:** `PROVIDER_LIVE_VERIFICATION.json` was a real execution snapshot unsuitable for public distribution.

**Action:** excluded by `open-source-prep`; retain provider contract tests and Mock mode.

**Status:** remediated.

### 4. Private/unclear media and fonts

**Finding:** experiment evidence contained MP4, WAV, frame/contact-sheet images and a cached OTF. Historical example screenshots included third-party platform/UI content with no standalone redistribution record.

**Action:** remove binary experiment evidence, third-party font copies and historical screenshots. Keep written findings, schemas and metrics. Replace only required screenshot fixtures with purpose-built solid-color synthetic PNGs.

**Status:** remediated; Markdown links are checked separately.

### 5. Absolute local paths and identity

**Finding:** 289 initial occurrences across reports, JSON evidence and old review documents revealed local directory structure/user name.

**Action:** remove real identities and rewrite remaining historical path strings to `${LOCAL_ROOT}` or `${EXTERNAL_VOLUME}` markers. Absolute media links were converted to “private local evidence not distributed” notes.

**Status:** remediated when final scan reports zero real local-home or mounted-volume path occurrences.

### 6. Dependency completeness and vulnerability

**Finding:** Python code/tests import Pillow but `requirements.txt` did not declare it. Fresh `npm ci` initially reported one high-severity transitive `source-map-js` denial-of-service advisory.

**Action:** add `Pillow>=10`; update the lockfile with `npm audit fix`; rerun TypeScript and audit.

**Status:** remediated; npm audit reports zero known vulnerabilities at audit time.

## Credential scan disposition

Pattern candidates in the final source were manually classified:

- `sk-fixture-activation-12345`: intentional fake redaction test value;
- `https://key:password@example.com`: intentional unsafe-URL rejection fixture;
- `hi@remotion.dev`: third-party text embedded in the installed Remotion player bundle, not a user address;
- empty variables in `.env.example`: configuration names only.

No real API key, access token, bearer value, password, private key, cookie or credential export was identified in the sanitized candidate.

## Repository mechanisms

| Mechanism | Result |
|---|---|
| `.env` | ignored; only empty `.env.example` tracked |
| SQLite/local data | ignored (`data/`, `*.db`, `*.sqlite*`) |
| build/cache/logs | ignored |
| private media/model/font patterns | ignored and removed from snapshot |
| symlinks | none |
| submodules / `.gitmodules` | none |
| Git LFS pointers | none |
| GitHub Actions | none in candidate |
| nested Git repositories | none in exported snapshot |

## Asset/license review

- Code and project-owned documentation: MIT.
- XIAO-Y master/action/element assets: project owner identified them as original project assets and elected MIT distribution for the copies in this repository.
- Third-party dependencies: keep their own licenses; lockfiles do not relicense them.
- External models, providers, system/third-party fonts, platform software and user evidence: not bundled and not relicensed.
- Historical screenshots with uncertain independent redistribution scope: removed.

See [ASSET_NOTICE.md](ASSET_NOTICE.md).

## Verification recorded before publication

- clean Python environment created from `requirements.txt`: PASS;
- full Python suite: `270 passed, 0 failed, 1 Starlette/httpx deprecation warning`;
- TypeScript `tsc --noEmit`: PASS;
- `npm audit`: 0 vulnerabilities after lockfile remediation;
- JSON parse check: PASS;
- workbench/render TestClient path: included in full suite and PASS after Node install;
- synthetic local voice boundary test: PASS.

Final link, secret, path, fresh-history, clean-clone and public-visibility checks are recorded in `CONTENT_OS_OPEN_SOURCE_RELEASE_REPORT.md` after repository publication.

## Residual limitations

- Pattern scanning cannot mathematically prove absence of every secret; fresh-history publication limits exposure to the audited tree.
- Historical text can name third-party tools/providers but does not bundle their credentials or grant rights.
- Real Provider/TTS/alignment/video QA execution requires external local configuration and was not repeated with private inputs.
- The synthetic fixtures verify contracts, not aesthetic quality.

## Publication gate

Publication is allowed only if all of the following remain true:

1. original repository visibility is Private;
2. public directory contains no original `.git` history or private remote;
3. final content scan and Markdown link check pass or every intentional unavailable artifact is clearly labeled;
4. tests and installation checks have recorded actual results;
5. public repository is created independently, not as a fork;
6. a clean clone reproduces the minimum test/startup path.

Any regression in these conditions changes the result to **PUBLICATION BLOCKED**.
