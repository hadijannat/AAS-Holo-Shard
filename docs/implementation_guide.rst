Implementation Guide
====================

Overview
--------

AAS-Holo-Shard supports two modes:

1. Pure-Python AAS JSON sharding: shard a single sensitive Property value and
   embed each shard into a valid AAS JSON file.
2. AASX encryption: encrypt the full package with AES-256-GCM, then split only
   the 32-byte key using Shamir's Secret Sharing (SSS).

Security gap addressed
----------------------

The IDTA Part 4 Security specification (June 2025) defines online access
control for AAS, but does not standardize file-level encryption for AASX
packages. This project provides a concrete, auditable pattern for
protecting AASX files at rest without relying on non-standard ZIP
encryption.

Market positioning
------------------

AAS-Holo-Shard sits at the intersection of:

- Digital twins and Industry 4.0 adoption
- European data sovereignty initiatives such as Gaia-X and Catena-X
- Multi-party supply chain collaboration and audit requirements

Use cases to highlight in a portfolio
-------------------------------------

- Supplier collaboration: OEM + tier suppliers share control over
  component specifications.
- Regulatory compliance: company + auditor threshold for audit access.
- Consortium research: academia + industry share custody for shared data.
- Battery passport workflows requiring secure lifecycle data sharing.

Architecture decisions
----------------------

1. AAS JSON sharding
   - Target a specific `idShort` and replace its value with `SHARD_V1:x:y`.
   - Each shard file remains a valid AAS JSON document.

2. Encrypt-then-share (AASX)
   - Encrypt full AASX bytes with AES-256-GCM.
   - Split only the 32-byte AES key (faster, safer, scalable).

3. Dual 16-byte SSS split (AASX)
   - PyCryptodome's SSS implementation operates on 16-byte secrets.
   - The AES key is split into two 16-byte halves and rejoined on combine.

4. Share custody
   - Shares are stored in distinct administrative or geographic domains
     (e.g., OEM + suppliers + auditor).

Security engineering notes
--------------------------

- Randomness: use `secrets` or `Crypto.Random.get_random_bytes`.
- Constant-time comparisons: `secrets.compare_digest` when verifying share
  material or integrity metadata.
- Memory hygiene: prefer `bytearray` for sensitive material; integrate
  zeroization libraries if required by your threat model.

Testing strategy
----------------

- Property-based tests (Hypothesis) validate encrypt/decrypt roundtrips.
- Coverage target is >= 90% for cryptography modules.
- Include known-good test vectors for interoperability checks.

Threat model notes
------------------

- Compromise of fewer than `threshold` shares must not reveal the key.
- Compromise of the encrypted payload alone must not reveal plaintext.
- Co-locating encrypted payload and shares defeats the model.

Implementation roadmap
----------------------

1. Pure-Python sharding (`src/aas_holo_shard/aas/shard.py` + `aas_shard.py`).
2. Core crypto module (`src/aas_holo_shard/core/shamir.py`).
3. AASX IO helpers (`src/aas_holo_shard/aas/parser.py`).
4. Storage adapters (`src/aas_holo_shard/storage/ipfs.py`).

Operational guidance
--------------------

- Store shares in distinct systems (HSM, IPFS, vaults, or physical custody).
- Log share access with tamper-evident audit trails.
- Use rotation policies for key re-splitting and share lifecycle management.
