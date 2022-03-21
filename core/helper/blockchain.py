import json
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

from core.block import Block, GenesisBlock
from core.transaction import CoinbaseTransaction
from core.wallet import Wallet

MIN_LONG_LONG = -9_223_372_036_854_775_807
MAX_LONG_LONG = 9_223_372_036_854_775_807


class BlockchainHelper:
    @staticmethod
    def load_blockchain() -> Block | None:
        try:
            with open('data/blockchain.bin', 'rb') as file:
                b = file.read()

                if len(b) == 0:
                    return None

                latest_block = GenesisBlock.from_bytes_chain(b)
        except FileNotFoundError:
            return None

        if not latest_block.valid(False):
            raise ValueError('Cannot load invalid blockchain')

        return latest_block

    @staticmethod
    def save_blockchain(latest_block: Block):
        assert isinstance(latest_block, Block), \
            'Latest block has to be an instance of Block.'

        with open('data/blockchain.bin', 'wb') as file:
            file.write(b''.join(bytes(block) for block in latest_block.expand_chain()))

    @staticmethod
    def export_blockchain(format: str, latest_block: Block):
        assert format == 'json', \
            'Currently supported export format is only "json".'
        assert isinstance(latest_block, Block), \
            'Latest block has to be an instance of Block.'

        if format == 'json':
            with open('data/blockchain.json', 'w') as file:
                json.dump([block.json() for block in latest_block.expand_chain()], file)

    @staticmethod
    def mine_block(
            latest_block: Block | None = None,
            wallet: Wallet | None = None,
            processes: int = 1,
            batch_size: int = int(1e6)
    ) -> Block | None:
        assert isinstance(latest_block, Block) or latest_block is None, \
            'Latest block has to be an instance of Block or None.'
        assert isinstance(wallet, Wallet) or wallet is None, \
            'Wallet has to be an instance of Wallet or None.'
        assert isinstance(processes, int) and processes >= 1, \
            'Processes has to be an int greater or equal to 1.'
        assert isinstance(batch_size, int) and batch_size >= 1, \
            'Batch size has to be an int greater or equal to 1.'

        from core.helper import TransactionHelper

        # Check if latest block is valid
        if isinstance(latest_block, Block) and not latest_block.valid(False):
            raise ValueError('Latest block must be valid or None.')

        # Load transactions from mempool and select only valid ones
        transactions = TransactionHelper.load_waiting_transactions()
        transactions = list(filter(lambda transaction: transaction.valid(latest_block), transactions))

        # Add coinbase transaction to transactions if wallet is specified
        if isinstance(wallet, Wallet):
            transactions.insert(0, CoinbaseTransaction(wallet.address()))

        # Create new block from the transactions
        block = Block(latest_block, transactions) if isinstance(latest_block, Block) else GenesisBlock(transactions)

        # Check validity of transactions
        if not block.valid_transactions():
            raise ValueError('Created block does not contain valid transactions after validation.')

        # Declare locked values and constants
        block_bytes = b''.join(bytes(b) for b in block.expand_chain())
        start = 0
        pending = set()

        # Start mining the block
        with ProcessPoolExecutor(processes) as executor:
            # Loop and process batch sizes until nonce is found
            # Max positive int size of int[8]
            while True and start <= MAX_LONG_LONG:
                if len(pending) >= processes:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)

                    found = list(filter(lambda result: result is not None, map(lambda future: future.result(), done)))

                    if len(found) > 0:
                        block.nonce = found[0]
                        return block

                pending.add(
                    executor.submit(
                        BlockchainHelper._process_nonce_batch,
                        block_bytes,
                        start,
                        start := min(start + batch_size, MAX_LONG_LONG),
                    )
                )

            # Terminate the pool
            executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _process_nonce_batch(block_bytes: bytes, start: int, end: int) -> int | None:
        assert isinstance(block_bytes, bytes) and len(block_bytes) > 0, \
            'Block bytes must be an instance of bytes.'
        assert isinstance(start, int) and isinstance(end, int) and start < end, \
            'Start and end must be instances of int and end must be greater than start.'

        # Copy the block to independently change nonce
        block = GenesisBlock.from_bytes_chain(block_bytes)

        # Iterate through assigned range of nonces
        for nonce in range(start, end):
            block.nonce = nonce

            # Check block validity
            if block.valid_proof():
                return nonce
