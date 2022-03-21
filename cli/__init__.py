from ._balance import balance
from ._transfer import transfer
from ._waiting_transactions import waiting_transactions
from ._create_wallet import create_wallet
from ._mine import mine

from ._app import app


def run() -> None:
    """
    Run commands for current runtime.
    """

    app()
