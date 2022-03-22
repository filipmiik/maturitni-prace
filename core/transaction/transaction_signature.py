from __future__ import annotations

from typing import Dict, Any, Tuple

from core.wallet import Wallet


class TransactionSignature:
    def __init__(self, wallet: Wallet, signature: bytes):
        """
        Create a transaction signature with provided wallet and signature (SHA256(signed transaction ID)).

        :param wallet: the wallet used to create the signature
        :param signature: the signature made in format SHA256(signed transaction ID)
        """

        assert isinstance(wallet, Wallet), \
            'Argument `wallet` has to be an instance of Wallet.'
        assert isinstance(signature, bytes) and len(signature) == 32, \
            'Argument `signature` has to be of type bytes[32].'

        self.wallet = wallet
        self.signature = signature

    def __bytes__(self):
        return bytes(self.wallet) + self.signature

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict[str, Any]:
        """
        Get the serialized transaction signature dumpable to JSON.

        :return: a dictionary containing all information about this signature
        """

        return {
            'script': bytes(self.wallet).hex(),
            'signature': self.signature.hex()
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> Tuple[bytes, TransactionSignature]:
        """
        Deserialize a transaction signature from provided bytes.

        :param b: the serialized signature bytes
        :return: a tuple containing the remaining bytes and the signature
        """

        # TODO: Refactor and change some assertions into exceptions due to user input
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'
        assert len(b) >= 526 + 32, \
            'Provided `b` argument cannot be deserialized.'

        b, script = b[526:], b[:526]
        b, signature = b[32:], b[:32]

        wallet = Wallet.load_by_script(script)

        return b, TransactionSignature(wallet, signature)
