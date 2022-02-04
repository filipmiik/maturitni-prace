from __future__ import annotations

from typing import SupportsBytes, Dict, Any

from core.wallet import Wallet


class TransactionSignature(SupportsBytes):
    def __init__(self, wallet: Wallet, signature: bytes):
        """
        Create a transaction signature with provided wallet and signature (SHA256(signed transaction ID)).

        :param wallet: the wallet used to create the signature
        :param signature: the signature made in format SHA256(signed transaction ID)
        """

        assert isinstance(wallet, Wallet), \
            'Provided `wallet` argument has to be instance of Wallet.'
        assert isinstance(signature, bytes) and len(signature) == 32, \
            'Provided `signature` argument has to be of type bytes[32].'

        self.wallet = wallet
        self.signature = signature

    def __bytes__(self):
        return bytes(self.wallet) + self.signature

    def __eq__(self, other: Any):
        return bytes(other) == self.__bytes__()

    def __hash__(self):
        return hash(self.__bytes__())

    def json(self) -> Dict:
        return {
            'script': bytes(self.wallet).hex(),
            'signature': self.signature.hex()
        }

    @classmethod
    def from_bytes(cls, b: bytes) -> (bytes, TransactionSignature):
        assert isinstance(b, bytes), \
            'Provided `b` argument has to be of type bytes.'
        assert len(b) >= 526 + 32, \
            'Provided `b` argument cannot be deserialized.'

        b, script = b[526:], b[:526]
        b, signature = b[32:], b[:32]

        wallet = Wallet.load_by_script(script)

        return b, TransactionSignature(wallet, signature)
