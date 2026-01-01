# AAS-Holo-Shard

[![PyPI](https://img.shields.io/pypi/v/aas-holo-shard.svg)](https://pypi.org/project/aas-holo-shard/)
[![Python](https://img.shields.io/pypi/pyversions/aas-holo-shard.svg)](https://pypi.org/project/aas-holo-shard/)
[![CI](https://github.com/username/aas-holo-shard/actions/workflows/ci.yml/badge.svg)](https://github.com/username/aas-holo-shard/actions)
[![codecov](https://codecov.io/gh/username/aas-holo-shard/branch/main/graph/badge.svg)](https://codecov.io/gh/username/aas-holo-shard)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

AAS-Holo-Shard secures Asset Administration Shell (AASX) packages at rest using a
threshold-cryptography workflow: encrypt the file, then split the encryption key
with Shamir's Secret Sharing (SSS). This eliminates single-key risk and enables
multi-party control over sensitive digital-twin data.

## Why this exists

The June 2025 IDTA Part 4 Security specification introduced online access control
for AAS, but file-level encryption remains unspecified. AAS-Holo-Shard fills that
gap with a practical, auditable pattern for protecting AASX files at rest.

## Core architecture

- Encrypt-then-share: AASX bytes are encrypted with AES-256-GCM.
- Threshold keys: only the 32-byte AES key is split; the file is never directly
  split (fast, scalable, and safer).
- Shard transport: share payloads are structured for storage in IPFS or any other
  content-addressed system.

## Quickstart

```python
from aas_holo_shard.core import shamir

aas_bytes = open("example.aasx", "rb").read()

encrypted, shares = shamir.encrypt_and_split(aas_bytes, threshold=3, total=5)

# Reconstruct with any 3 shares
plaintext = shamir.reconstruct_and_decrypt(encrypted, shares[:3])
assert plaintext == aas_bytes
```

## Optional integrations

- BaSyx SDK: `aas_holo_shard.aas.parser.load_aasx_basyx` loads AASX files into
  BaSyx object and file stores.
- IPFS: `aas_holo_shard.storage.ipfs.store_shares` stores share payloads in a
  local IPFS daemon (requires `ipfshttpclient`).

## Project layout

```
AAS-Holo-Shard/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── codeql.yml
│   │   └── release.yml
│   ├── SECURITY.md
│   ├── CONTRIBUTING.md
│   └── dependabot.yml
├── docs/
├── src/
│   └── aas_holo_shard/
│       ├── __init__.py
│       ├── core/shamir.py
│       ├── aas/parser.py
│       └── storage/ipfs.py
├── tests/
│   ├── test_shamir.py
│   ├── test_vectors/
│   └── conftest.py
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
pre-commit install
pytest
```

## Security notes

- Use `secrets` or `Crypto.Random.get_random_bytes` for randomness.
- Never store shares with the encrypted payload in the same location.
- Prefer hardware-backed or multi-party custody for share storage.

## Docs

See `docs/implementation_guide.rst` for the full architecture, testing
requirements, and integration roadmap.

## License

Apache-2.0. See `LICENSE` for details.
