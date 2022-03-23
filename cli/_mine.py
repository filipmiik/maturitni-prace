import typer

from core.block import Block
from core.helpers import BlockchainHelper, TransactionHelper
from core.transaction import Transaction
from ._app import app
from ._helper import CLIHelper


@app.command()
def mine(
        address: str = typer.Argument(..., help='The wallet address to transfer new coins to')
) -> None:
    """
    Mine new block and add it to the blockchain. Coinbase transaction is awarded to ADDRESS.
    """

    # Parse command arguments
    wallet = CLIHelper.load_wallet_by_address(address)

    # Check if blockchain is initialized
    latest_block = BlockchainHelper.load_blockchain()

    # Mine the block
    print(f'Mining new block...')

    mined_block = BlockchainHelper.mine_block(latest_block, wallet)

    # Check if able to mine block
    if isinstance(mined_block, Block):
        # Save the blockchain
        BlockchainHelper.save_blockchain(mined_block)
        BlockchainHelper.export_blockchain(mined_block)

        # Remove processed transactions from mempool
        TransactionHelper.remove_transactions(mined_block.transactions)

        # Print success message and block details
        prev_block_id = mined_block.previous_block.id().hex() if isinstance(mined_block.previous_block, Block) else None

        print(f'Successfully mined a new block.\n\nBlock details:')
        print(f'├ ID: {mined_block.id().hex()}')
        print(f'├ Nonce: {mined_block.nonce}')
        print(f'├ Timestamp: {mined_block.timestamp}')
        print(f'├ Transactions: {len(mined_block.transactions)}')
        print(f'├ Merkle root: {Transaction.calculate_merkle_root(mined_block.transactions).hex()}')
        print(f'└ Previous block ID: {prev_block_id}')
        return

    print(f'Failed to mine block. Try again.')
