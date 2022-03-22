from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from typing import TYPE_CHECKING

from core.transaction import CoinbaseTransaction
from core.wallet import Wallet

if TYPE_CHECKING:
    from core.block import Block, GenesisBlock

MIN_INT64 = -9_223_372_036_854_775_807
MAX_INT64 = 9_223_372_036_854_775_807


class BlockchainHelper:
    @staticmethod
    def load_blockchain() -> Block | None:
        """
        Load blockchain from the store.

        :return: the latest block or None if blockchain not initialized
        """

        from core.block import GenesisBlock

        # Load serialized blockchain and deserialize it
        try:
            with open('data/blockchain.bin', 'rb') as file:
                if len(b := file.read()) == 0:
                    return None

                latest_block = GenesisBlock.from_bytes_chain(b)
        except FileNotFoundError:
            return None

        # Prevent loading invalid blockchain into the application
        if not latest_block.valid(False):
            raise ValueError('Cannot load invalid blockchain.')

        return latest_block

    @staticmethod
    def save_blockchain(latest_block: Block) -> None:
        """
        Save serialized blockchain to the store from provided latest block (overwrites blockchain store).

        :param latest_block: the latest block to be saved
        """

        from core.block import Block

        assert isinstance(latest_block, Block), \
            'Argument `latest_block` has to be an instance of Block.'

        # Save the serialized and expanded blockchain
        with open('data/blockchain.bin', 'wb') as file:
            file.write(b''.join(bytes(block) for block in latest_block.expand_chain()))

    @staticmethod
    def export_blockchain(latest_block: Block) -> None:
        """
        Export provided latest block to JSON (overwrites blockchain export store).

        :param latest_block: the latest block to be exported
        """

        from core.block import Block

        assert isinstance(latest_block, Block), \
            'Argument `latest_block` has to be an instance of Block.'

        # Save the serialized and expanded blockchain
        with open('data/blockchain.json', 'w') as file:
            json.dump(list(block.json() for block in latest_block.expand_chain()), file)

    @staticmethod
    def mine_block(
            latest_block: Block | None = None,
            wallet: Wallet | None = None,
            processes: int = 1,
            batch_size: int = int(1e6)
    ) -> Block | None:
        """
        Attempt to mine a new block with transactions from mempool.

        :param latest_block: the latest block after which a new block should be created or None if mining genesis block
        :param wallet: the wallet to which the mining reward will be awarded
        :param processes: the maximum number of processes to run in parallel while mining
        :param batch_size: the batch size of nonces in which to validate the new block
        :return: the new block or None if no valid nonce was found
        """

        from core.block import Block, GenesisBlock
        from core.helpers import TransactionHelper

        assert isinstance(latest_block, Block) or latest_block is None, \
            'Argument `latest_block` has to be an instance of Block or None.'
        assert isinstance(wallet, Wallet) or wallet is None, \
            'Argument `wallet` has to be an instance of Wallet or None.'
        assert isinstance(processes, int) and processes >= 1, \
            'Argument `processes` has to be an int greater or equal to 1.'
        assert isinstance(batch_size, int) and batch_size >= 1, \
            'Argument `batch_size` has to be an int greater or equal to 1.'

        # Check if latest block is valid
        if isinstance(latest_block, Block) and not latest_block.valid(False):
            raise ValueError('Latest block has to be valid.')

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
            raise Exception('Created block does not contain valid transactions after validation.')

        # Declare locked values and constants
        block_bytes = b''.join(bytes(b) for b in block.expand_chain())
        start = 0
        pending = set()

        # Start mining the block
        with ProcessPoolExecutor(processes) as executor:
            # Loop and process batch sizes until nonce is found
            # Max positive int size of int[8]
            while True and start <= MAX_INT64:
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
                        start := min(start + batch_size, MAX_INT64),
                    )
                )

            # Terminate the pool
            executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _process_nonce_batch(block_bytes: bytes, start: int, end: int) -> int | None:
        """
        Worker function for validating block with a range of nonces.

        :param block_bytes: a serialized block
        :param start: the lowest value of tested nonces (inclusive)
        :param end: the highest value of tested nonces (exclusive)
        :return: a found nonce or None if no valid was found
        """

        from core.block import GenesisBlock

        assert isinstance(block_bytes, bytes) and len(block_bytes) > 0, \
            'Argument `block_bytes` has to be of type bytes.'
        assert isinstance(start, int) and isinstance(end, int) and start < end, \
            'Arguments `start` and `end` have to be of type int and end > start.'

        # Deserialize the block data
        block = GenesisBlock.from_bytes_chain(block_bytes)

        # Iterate through assigned range of nonces
        for nonce in range(start, end):
            block.nonce = nonce

            # Check block validity
            if block.valid_proof():
                return nonce
