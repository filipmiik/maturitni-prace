from core.wallet import Wallet


class CLIHelper:
    @staticmethod
    def load_wallet_by_address(address: str) -> Wallet:
        """
        Safely load wallet from register by address in hex format from user input.

        :param address: the wallet's address
        :return: the loaded wallet
        """

        assert isinstance(address, str), \
            'Argument `address` has to be of type str.'

        try:
            address = bytes.fromhex(address)
        except ValueError:
            raise ValueError('Wallet address must be a valid hex string.')

        return Wallet.load_from_address(address)
