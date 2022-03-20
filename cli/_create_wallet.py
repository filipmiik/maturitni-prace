from core.wallet import Wallet
from ._app import app


@app.command()
def create_wallet() -> None:
    """
    Create new wallet and save it into the registry.
    """

    # Create new wallet
    print(f'Creating new wallet...')

    wallet = Wallet.create_new_wallet()

    # Print the wallet's address
    print(f'\nWallet address: {wallet.address().hex()}')
