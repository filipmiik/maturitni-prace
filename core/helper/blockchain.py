from core.block import Block, GenesisBlock


class BlockchainHelper:
    @staticmethod
    def load_blockchain() -> Block:
        with open('data/blockchain.bin', 'rb') as file:
            latest_block = GenesisBlock.from_bytes_chain(file.read())

        # if not latest_block.check_proof() or not latest_block.check_transactions():
        if not latest_block.check_transactions():
            raise ValueError('Cannot load invalid blockchain')

        return latest_block

    @staticmethod
    def save_blockchain(latest_block: Block):
        assert isinstance(latest_block, Block), \
            'Latest block has to be an instance of Block.'

        pass

    @staticmethod
    def export_blockchain(type: str, latest_block: Block):
        assert type == 'json', \
            'Currently supported export type is only "json".'
        assert isinstance(latest_block, Block), \
            'Latest block has to be an instance of Block.'

        pass
