from hashlib import sha256
from typing import Sequence, List


def calculate_merkle_root(leaves: Sequence[bytes]) -> bytes:
    assert isinstance(leaves, Sequence) and len(leaves) > 0, \
        "Parameter `leaves` is required to have at least one item."

    branches: List[bytes] = list(leaves)

    while len(branches) > 1:
        if (len(branches) % 2) != 0:
            branches.append(b'')

        branches = [sha256(a + b).digest() for a, b in zip(branches[0::2], branches[1::2])]

    return branches[0]
