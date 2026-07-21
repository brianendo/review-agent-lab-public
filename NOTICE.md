# Third-party code in the evalset

Several evalset cases include source snapshots of open-source projects at a
specific commit, used as realistic review context. Each is redistributed under
its own permissive license, with attribution below. All are unmodified snapshots
except for the single seeded/reverted line documented in that case's
`manifest.json`.

| Case(s) | Project | License |
|---|---|---|
| `httpx-cancel-close` | [encode/httpx](https://github.com/encode/httpx) | BSD-3-Clause |
| `requests-scheme` | [psf/requests](https://github.com/psf/requests) | Apache-2.0 |
| `anyio-capacitylimiter-inf` | [agronholm/anyio](https://github.com/agronholm/anyio) | MIT |
| `pydantic-falsy-alias` | [pydantic/pydantic](https://github.com/pydantic/pydantic) | MIT |
| `click-choice-brackets`, `clean-click-zfs` | [pallets/click](https://github.com/pallets/click) | BSD-3-Clause |
| `rich-ansi-newlines`, `clean-rich-expandable`, `clean-rich-linkids` | [Textualize/rich](https://github.com/Textualize/rich) | MIT |

Each snapshot's `repo/` directory includes the project's own LICENSE file, as
those licenses require for redistribution.

Each "natural bug" case reverses a real merged fix from the linked project (the
diff under review is the fix inverted); the linked PR/issue is recorded in the
case manifest. No production secrets are included — snapshots are filtered to
source files and exclude data, `.git`, and environment files.
