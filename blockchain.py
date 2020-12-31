import hashlib
import json
from textwrap import dedent
from time import time

from uuid import uuid4

from flask import Flask, jsonify, request


class BlockChain ():
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block (first block in the chain)
        self.new_block(previous_hash=1, proof=100)

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



{"chain":[{"index":1,"previous_hash":1,"proof":100,"timestamp":1609395990.8798,"transactions":[]},{"index":2,"previous_hash":"c13bc94329551b5457313f4754c3e1a19d782bdf69d1209f3db868a0ae32489f","proof":35293,"timestamp":1609396010.814421,"transactions":[{"amount":1,"recipient":"91a9d382fe744c46921db6346af6cc28","sender":0}]},{"index":3,"previous_hash":"4bae36d164a23477c4a53f82d4678d96b538eaa9cb170d584288e7fb0fe4159a","proof":35089,"timestamp":1609396051.359301,"transactions":[{"amount":1,"recipient":"91a9d382fe744c46921db6346af6cc28","sender":0}]},{"index":4,"previous_hash":"7871eea94f8ffb82d6a80caf81358aecd31282887ee2f0c6311f154518670cdb","proof":119678,"timestamp":1609396053.4126348,"transactions":[{"amount":1,"recipient":"91a9d382fe744c46921db6346af6cc28","sender":0}]}],"length":4}