from __future__ import annotations

import errno
import os
import sys
from hashlib import sha256
from typing import TYPE_CHECKING

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.padding import PSS, MGF1
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key, RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption, \
    load_pem_private_key

if TYPE_CHECKING:
    from core.transaction import Transaction, TransactionSignature


class Wallet:
    def __init__(self, private_key: RSAPrivateKey):
        """
        Create Wallet instance with private key (private key ~ Wallet).

        :param private_key: the represented private key
        """

        assert isinstance(private_key, RSAPrivateKey), \
            'Argument `private_key` has to be an instance of RSAPrivateKey.'

        self._private_key = private_key

    def __bytes__(self):
        return self.public_key().public_bytes(encoding=Encoding.DER, format=PublicFormat.PKCS1)

    def __eq__(self, other):
        return bytes(other) == self.__bytes__() or bytes(other) == self.address()

    def __hash__(self):
        return hash(self.__bytes__())

    def address(self) -> bytes:
        """
        Calculate the wallet's address.

        :return: the first 8 bytes of the hash digest of the wallet's public representation
        """

        return sha256(self.__bytes__()).digest()[:8]

    def public_key(self) -> RSAPublicKey:
        """
        Export the wallet's public key.

        :return: the public key derived from stored private key
        """

        return self._private_key.public_key()

    def save(self) -> None:
        """
        Save the wallet into the registry.

        :raises FileExistsError: if wallet is already saved
        :raises RuntimeError: if failed to save the wallet
        """

        address = self.address().hex()
        wallet_directory = os.path.join(os.path.realpath(sys.path[0]), r'data/wallets', address)

        # Check if wallet with this ID is not already saved
        if os.path.exists(wallet_directory):
            raise FileExistsError(f'Wallet {address} is already saved and cannot be overwritten.')

        try:
            # Create wallet directory if not created
            self._create_wallet_directory()

            # Save the private key
            with open(os.path.join(wallet_directory, 'private.pem'), 'wb') as key_file:
                private_key_bytes = self._private_key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.PKCS8,
                    encryption_algorithm=NoEncryption()
                )

                key_file.write(private_key_bytes)
        except Exception:
            raise RuntimeError(f'Failed to save wallet {address} to the registry.')

    def sign_transaction(self, transaction: Transaction) -> None:
        """
        Sign a transaction using private key stored in this Wallet.

        :param transaction: the transaction to be signer
        """

        from core.transaction import Transaction, TransactionSignature

        assert isinstance(transaction, Transaction), \
            'Argument `transaction` has to be an instance of Transaction.'

        # Create the signature from store private key and SHA256(transaction)
        signature = self._private_key.sign(
            data=transaction.id(),
            padding=PSS(
                mgf=MGF1(hashes.SHA256()),
                salt_length=PSS.MAX_LENGTH
            ),
            algorithm=hashes.SHA256()
        )
        signature = sha256(signature).digest()

        # Sign the transaction with just created signature and this wallet
        transaction.sign(TransactionSignature(self, signature))

    def _create_wallet_directory(self) -> None:
        """
        Create wallet directory in the registry. The wallet directory name will match the wallet address.
        """

        address = self.address().hex()

        try:
            # Try to create the directory
            os.makedirs(os.path.join(os.path.realpath(sys.path[0]), r'data/wallets', address))
        except OSError as exception:
            # Allow propagation of "directory already exists" error
            if exception.errno != errno.EEXIST:
                raise

            raise RuntimeError(f'Failed to create wallet directory for {address}.')

    @classmethod
    def create_new_wallet(cls) -> Wallet:
        """
        Safely create new wallet and save it to the registry.

        :return: the newly created wallet
        """

        # Generate new private key that does not collide with existing one
        private_key = Wallet.generate_new_private_key()

        # Create the wallet instance and save it to the registry
        wallet = cls(private_key)
        wallet.save()

        return wallet

    @classmethod
    def load_from_address(cls, address: bytes) -> Wallet:
        """
        Safely load wallet by address from the registry.

        :param address: the wallet address (8 bytes)
        :raises FileNotFoundError: if wallet with such ID was not found
        :return: the loaded wallet
        """

        assert isinstance(address, bytes) and len(address) == 8, \
            'Argument `address` has to be of type bytes[8].'

        try:
            # Try to load the private key from registry
            with open(
                    os.path.join(
                        os.path.realpath(sys.path[0]),
                        r'data/wallets',
                        address.hex(),
                        'private.pem'
                    ),
                    'rb'
            ) as key_file:
                private_key = load_pem_private_key(
                    data=key_file.read(),
                    password=None,
                    backend=crypto_default_backend()
                )

                return cls(private_key)
        except Exception:
            raise FileNotFoundError(f'Wallet with address {address.hex()} was not found in the registry.')

    @classmethod
    def load_by_script(cls, script: bytes) -> Wallet:
        """
        Safely load wallet by public wallet representation from the registry.

        :param script: the wallet's representation in bytes
        :return: the loaded wallet
        """

        address = sha256(script).digest()[:8]

        return cls.load_from_address(address)

    @staticmethod
    def generate_new_private_key() -> RSAPrivateKey:
        """
        Safely generate new wallet private key that does not collide with existing one.

        :return: the generated private key
        """

        root_path = os.path.realpath(sys.path[0])

        private_key = None
        address = None

        # Keep creating new private keys until it does not collide with one already created
        while address is None or os.path.isdir(os.path.join(root_path, fr'data/wallets/{address}')):
            # Generate a new private key
            private_key = generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=crypto_default_backend()
            )

            # Get wallet address
            wallet = Wallet(private_key)
            address = wallet.address()

        return private_key
