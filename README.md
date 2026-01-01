# AAS-Holo-Shard

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/hadijannat/AAS-Holo-Shard)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/hadijannat/AAS-Holo-Shard/actions/workflows/ci.yml/badge.svg)](https://github.com/hadijannat/AAS-Holo-Shard/actions)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

AAS-Holo-Shard secures Asset Administration Shell data using threshold
cryptography. It supports two complementary modes:

- Pure-Python AAS JSON sharding: shatter a single sensitive field into
  mathematical shards stored inside valid AAS files.
- AES-GCM AASX encryption: encrypt the full package, then split only the
  32-byte key with Shamir's Secret Sharing (SSS).

## Research context

**The Problem:** Industry 4.0 architectures are centralized points of failure.
If an AAS file contains a trade secret, it exists in plaintext. If the file is
stolen, the secret is lost. If the server goes down, the Digital Twin dies.

**The Research Question:**
"How can we store a critical Asset Administration Shell so that no single entity
possesses the data, yet the data can be reconstructed instantly when a consensus
of stakeholders (e.g., 3 out of 5) agree to collaborate?"

**The Novel Solution:** implement Shamir's Secret Sharing to shard only the
sensitive submodel value. Each shard is a valid AAS file, but the sensitive field
is replaced by a mathematical coordinate with no standalone meaning.

The June 2025 IDTA Part 4 Security specification introduced online access control
for AAS, but file-level encryption remains unspecified. AAS-Holo-Shard fills that
gap with a practical, auditable pattern for protecting AASX files at rest.

## Core architecture

- AAS JSON sharding: replace a target `idShort` value with `SHARD_V1:x:y` in
  N shard files; any K shards can reconstruct the secret.
- Encrypt-then-share (AASX): AES-256-GCM encrypts the package, then only the
  32-byte key is split (fast, scalable, safer).
- Share custody: distribute shards across independent stakeholders or systems.

## Quickstart

### AAS JSON sharding (pure Python)

Create a demo AAS file:

```bash
python aas_shard.py split factory.json MasterKey -n 3 -k 2
```

Reconstruct with any 2 shards:

```bash
python aas_shard.py combine MasterKey factory_shard_1.json factory_shard_3.json
```

## Install

```bash
pip install aas-holo-shard
```

Optional extras:

```bash
pip install "aas-holo-shard[crypto]"
pip install "aas-holo-shard[basyx]"
pip install "aas-holo-shard[ipfs]"
```

### AASX encryption (optional dependency)

```python
from aas_holo_shard.core import shamir

aas_bytes = open("example.aasx", "rb").read()

encrypted, shares = shamir.encrypt_and_split(aas_bytes, threshold=3, total=5)

# Reconstruct with any 3 shares
plaintext = shamir.reconstruct_and_decrypt(encrypted, shares[:3])
assert plaintext == aas_bytes
```

## Optional integrations

- AES-GCM AASX mode: `pip install "aas-holo-shard[crypto]"`.
- BaSyx SDK: `pip install "aas-holo-shard[basyx]"`.
- IPFS: `pip install "aas-holo-shard[ipfs]"`.

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
├── factory.json
├── aas_shard.py
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
