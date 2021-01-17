import hashlib
import json
from textwrap import dedent
from time import time

from uuid import uuid4

from flask import Flask, jsonify, request

from urllib.parse import urlparse


class BlockChain ():
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # Create the genesis block (first block in the chain)
        self.new_block(previous_hash=1, proof=100)

    def register_new_node(self, address):
        """
        Register a new node so it can be added to the decentrilized network.
        :param: addreess: <str> Address of node. ex: 'http://192.134.0.7:8000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def is_valid_chain(self, chain):
        """
        Determine if a given blockchain is valid (all the blocks were made and linked in order)
        :param chain: <list> a blockchain
        :return: <bool> True if valid, False otherwise
        """
        last_block = chain[0]
        for current_index in range(1, len(chain)):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print(f'==============')
            # check that the hast of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block

        return True

    def resolve_conflicts(self):
        """
        This is the CONSENSUS ALGORITHM. It resolves conflicts by 
        replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None
        # We're only looking for chains longer than ours
        max_lenght = len(self.chain)

        # Get the other chains in the network and verify they are valid
        for node in neighbours:
            respose = requests.get(f'http//{node}/chain')
            if respose.status_code == 200:
                lenght = respose.json()['length']
                chain = respose.json()['chain']

                # check if the length is longer and the chain is valid
                if lenght > max_lenght and self.is_valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the BlockChain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }

        # reset the current_transactions list ?? IDK why we do this
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined block
        :param sender: <str> Address of the sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return <int> The index of the block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        """
        returns the last block in the chain
        """
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """Creats a SHA-256 hash of a block
        :param block: <dict> Block object
        :return: <str>
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm
        - Find a number p such that hasg(pp') contains 4 leading zeros
        where p is the previous p'
        - p is the previous proof and p' is the new proof
        :return: <int>
        """
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does Hash(last_proof, proof) contain 4 leading zeros?
        :param last_proof: <int> Previous proof
        :param proff: <int> Current Proof
        :return: <bool> True if correct, False if not
        """
        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"


app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Generate a globally unique adress for this node

node_identifier = str(uuid4()).replace('-', '')

blockchain = BlockChain()


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']

    proof = blockchain.proof_of_work(last_proof)

    # the sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(sender=0, recipient=node_identifier, amount=1)

    # Forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "NEW BLOCK FORGED!",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@ app.route('/transactions/new', methods=['POST'])
def new_transactions():
    """
    This is what a user would send to the transaction endpoint
    {
     "sender": "my address",
     "recipient": "someone else's address",
     "amount": 5
    }
    """
    values = request.get_json()

    # make sure the required fields are filled out
    required = ['sender', 'recipient', 'amount']
    if not all(info in values for info in required):
        return 'Missing Values', 400
    # Create a new transaction
    index = blockchain.new_transaction(
        values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}

    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='localhost', port=5000)


@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    values = request.get_json()
    nodes = values.get['nodes']
    if nodes is None:
        return "Error: Please supply a valid list of nodes" 400

    for node in nodes:
        blockchain.register_new_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_ndes': list(blockchain.nodes)
    }
    return jsonify(response) 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
<<<<<<< HEAD
    return jsonify(response), 200
=======
>>>>>>> 7eb08d4dbd6391762d6297a205e43a3f4ecdc9fb
