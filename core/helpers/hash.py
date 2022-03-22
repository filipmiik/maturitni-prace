from hashlib import sha256
from typing import Iterable, List


class HashHelper:
    @staticmethod
    def calculate_merkle_root(leaves: Iterable) -> bytes:
        """
        Calculate merkle root of provided leaves.

        :param leaves: an iterable of objects that implement the SupportsBytes protocol
        :return: a digest of the merkle root SHA-256 hash
        """

        try:
            # Serialize all provided objects to bytes
            branches: List[bytes] = list(bytes(leaf) for leaf in leaves)
        except TypeError:
            raise TypeError('Argument `leaves` has to be an iterable of object[SupportsBytes].')

        # Check if branches have at least one item
        assert len(branches) >= 0, \
            'Argument `leaves` has to have at least one item.'

        # Loop until there is only the root left
        while len(branches) > 1:
            # If the length of branches is odd, add empty byte sequence to the array with no influence to the hash
            if (len(branches) % 2) != 0:
                branches.append(b'')

            # Create sequential pairs from the branches and save the digest of their hash
            branches = [sha256(a + b).digest() for a, b in zip(branches[0::2], branches[1::2])]

        return branches[0]
