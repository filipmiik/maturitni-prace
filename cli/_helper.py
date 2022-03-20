from core.wallet import Wallet


class CLIHelper:
    @staticmethod
    def load_wallet_by_address(address: str) -> Wallet:
        assert isinstance(address, str), \
            'Provided address has to be of type str.'

        try:
            address = bytes.fromhex(address)
        except ValueError:
            raise ValueError('Wallet address must be a valid hex string.')

        return Wallet.load_from_address(address)
