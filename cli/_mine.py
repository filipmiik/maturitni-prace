import typer

from ._app import app


@app.command()
def mine(
        address: str = typer.Argument(..., help='The wallet address to transfer new coins to')
) -> None:
    """
    Mine new block and add it to the blockchain. Coinbase transaction is awarded to ADDRESS.
    """

    print(f'Mining block... New coins are transferred to: {address}')
