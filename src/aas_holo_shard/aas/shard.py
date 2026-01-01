"""Pure-Python Shamir sharding for AAS JSON files."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union

PRIME = 2**521 - 1
SHARD_PREFIX = "SHARD_V1"

Shard = Tuple[int, int]


def _eval_poly(poly: Sequence[int], x: int) -> int:
    result = 0
    for coeff in reversed(poly):
        result = (result * x + coeff) % PRIME
    return result


def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:
        q, b, a = b // a, a, b % a
        y0, y1 = y1, y0 - q * y1
        x0, x1 = x1, x0 - q * x1
    return b, x0, y0


def _mod_inverse(k: int) -> int:
    g, x, _ = _extended_gcd(k % PRIME, PRIME)
    if g != 1:
        raise ValueError("modular inverse does not exist")
    return x % PRIME


def make_shards(secret_int: int, n: int, k: int) -> List[Shard]:
    if k < 1 or n < 1:
        raise ValueError("n and k must be >= 1")
    if k > n:
        raise ValueError("k cannot be greater than n")
    if secret_int >= PRIME:
        raise ValueError("secret is too large for the chosen prime field")

    poly = [secret_int] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
    shards: List[Shard] = []
    for i in range(1, n + 1):
        y = _eval_poly(poly, i)
        shards.append((i, y))
    return shards


def recover_secret(shards: Iterable[Shard]) -> int:
    shard_list = list(shards)
    if not shard_list:
        raise ValueError("at least one shard is required")

    x_s, y_s = zip(*shard_list)
    secret = 0

    for j, (xj, yj) in enumerate(zip(x_s, y_s)):
        numerator = 1
        denominator = 1
        for m, xm in enumerate(x_s):
            if m == j:
                continue
            numerator = (numerator * (-xm)) % PRIME
            denominator = (denominator * (xj - xm)) % PRIME
        lagrange = (numerator * _mod_inverse(denominator)) % PRIME
        secret = (secret + yj * lagrange) % PRIME

    return secret


def str_to_int(value: str) -> int:
    return int.from_bytes(value.encode("utf-8"), "big")


def int_to_str(value: int) -> str:
    if value == 0:
        return ""
    length = (value.bit_length() + 7) // 8
    return value.to_bytes(length, "big").decode("utf-8")


def find_element(aas_json: Any, id_short: str) -> Optional[dict]:
    if isinstance(aas_json, dict):
        if aas_json.get("idShort") == id_short and "value" in aas_json:
            return aas_json
        for item in aas_json.values():
            found = find_element(item, id_short)
            if found is not None:
                return found
    elif isinstance(aas_json, list):
        for item in aas_json:
            found = find_element(item, id_short)
            if found is not None:
                return found
    return None


def _parse_shard_value(raw_value: str) -> Optional[Shard]:
    if not raw_value.startswith(f"{SHARD_PREFIX}:"):
        return None
    parts = raw_value.split(":")
    if len(parts) != 3:
        return None
    return int(parts[1]), int(parts[2])


def _inject_shard_value(element: dict, shard: Shard) -> None:
    x, y = shard
    element["value"] = f"{SHARD_PREFIX}:{x}:{y}"
    element["description"] = [
        {
            "language": "en",
            "text": "ENCRYPTED HOLOGRAPHIC SHARD - UNREADABLE ALONE",
        }
    ]


def split_aas(
    file_path: Union[str, Path],
    target_id: str,
    n: int,
    k: int,
) -> List[Path]:
    source_path = Path(file_path)
    original_aas = json.loads(source_path.read_text())

    target_elem = find_element(original_aas, target_id)
    if not target_elem:
        raise ValueError(f"element '{target_id}' not found")

    secret_val = str(target_elem["value"])
    secret_int = str_to_int(secret_val)
    if secret_int >= PRIME:
        raise ValueError("secret is too long for the current prime field")

    shards = make_shards(secret_int, n, k)
    output_paths: List[Path] = []

    for idx, shard in enumerate(shards, start=1):
        shard_aas = json.loads(json.dumps(original_aas))
        elem = find_element(shard_aas, target_id)
        if elem is None:
            raise ValueError("target element disappeared during copy")
        _inject_shard_value(elem, shard)

        out_name = source_path.with_name(f"{source_path.stem}_shard_{idx}.json")
        out_name.write_text(json.dumps(shard_aas, indent=2))
        output_paths.append(out_name)

    return output_paths


def combine_aas(
    files: Iterable[Union[str, Path]],
    target_id: str,
    output: Union[str, Path],
) -> str:
    raw_shards: List[Shard] = []
    files_list = [Path(path) for path in files]

    for path in files_list:
        data = json.loads(path.read_text())
        elem = find_element(data, target_id)
        if not elem:
            continue
        value = str(elem.get("value", ""))
        shard = _parse_shard_value(value)
        if shard:
            raw_shards.append(shard)

    if not raw_shards:
        raise ValueError("no valid shards found")

    recovered_int = recover_secret(raw_shards)
    try:
        recovered_str = int_to_str(recovered_int)
    except UnicodeDecodeError as exc:
        raise ValueError("reconstructed secret is not valid UTF-8") from exc

    restored_aas = json.loads(files_list[0].read_text())
    elem = find_element(restored_aas, target_id)
    if elem is None:
        raise ValueError("target element not found in restored file")
    elem["value"] = recovered_str
    elem.pop("description", None)

    output_path = Path(output)
    output_path.write_text(json.dumps(restored_aas, indent=2))
    return recovered_str


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AAS Holo-Shard (pure Python)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    split_p = subparsers.add_parser("split", help="Split AAS into N shards")
    split_p.add_argument("file", help="Input AAS JSON file")
    split_p.add_argument("id", help="idShort of Property to encrypt")
    split_p.add_argument("-n", type=int, default=3, help="Total shards")
    split_p.add_argument("-k", type=int, default=2, help="Threshold needed")

    join_p = subparsers.add_parser("combine", help="Combine shards")
    join_p.add_argument("id", help="idShort of Property to recover")
    join_p.add_argument("files", nargs="+", help="List of shard files")
    join_p.add_argument(
        "-o",
        "--output",
        default="restored_aas.json",
        help="Output file for restored AAS",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "split":
            output_paths = split_aas(args.file, args.id, args.n, args.k)
            print(f"Split into {len(output_paths)} shards")
            for path in output_paths:
                print(f"  {path}")
            return 0

        if args.command == "combine":
            recovered = combine_aas(args.files, args.id, args.output)
            print("Reconstruction successful")
            print(f"Recovered: {recovered}")
            print(f"Saved: {args.output}")
            return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
