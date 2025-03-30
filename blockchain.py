import hashlib
import json
import requests
import time
from uuid import uuid4
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
import threading
from datetime import datetime
import pytz

# Enhanced Constants
MINING_DIFFICULTY = 4  # Adjusts dynamically
MINING_SENDER = "MINER_REWARD"
INITIAL_MINER_REWARD = 50
HALVING_INTERVAL = 210000  # Blocks
INITIAL_BALANCE = 100
BLOCK_TIME_TARGET = 60  # 1 minute blocks
DIFFICULTY_ADJUSTMENT_INTERVAL = 2016  # Blocks

class Blockchain:
    def __init__(self):
        self.transactions = []
        self.chain = []
        self.nodes = set()
        self.wallets = defaultdict(lambda: INITIAL_BALANCE)
        self.transaction_history = defaultdict(list)
        self.smart_contracts = {}
        self.node_id = str(uuid4()).replace('-', '')
        self.network_graph = nx.Graph()
        self.network_graph.add_node(self.node_id)
        self.mining_reward = INITIAL_MINER_REWARD
        self.block_time_history = []
        self.create_block(nonce=0, previous_hash='00')  # Genesis block
        self.start_block_time_monitor()
        
    def verify_transaction_signature(self, sender_address, signature, transaction):
        """Verify the signature of a transaction using ECDSA"""
        try:
            # Reconstruct the verifying key from the sender's address
            verifying_key = VerifyingKey.from_string(bytes.fromhex(sender_address), curve=SECP256k1)
            
            # Prepare the message to verify (transaction data without signature)
            tx_copy = transaction.copy()
            tx_copy.pop('signature', None)  # Remove signature if present
            message = json.dumps(tx_copy, sort_keys=True).encode()
            
            # Verify the signature
            return verifying_key.verify(bytes.fromhex(signature), message)
        except:
            return False

    def calculate_merkle_root(self):
        """Calculate the Merkle root of all transactions in the current block"""
        if not self.transactions:
            return "0" * 64  # Return empty hash if no transactions
            
        transaction_hashes = [hashlib.sha256(json.dumps(tx).encode()).hexdigest() for tx in self.transactions]
        
        # Build the merkle tree
        while len(transaction_hashes) > 1:
            new_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                if i + 1 < len(transaction_hashes):
                    combined = transaction_hashes[i] + transaction_hashes[i+1]
                else:
                    combined = transaction_hashes[i] + transaction_hashes[i]  # Duplicate if odd number
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            transaction_hashes = new_hashes
            
        return transaction_hashes[0]

    def calculate_difficulty(self):
        """Dynamic difficulty adjustment similar to Bitcoin"""
        if len(self.chain) % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 and len(self.chain) > 0:
            prev_adjustment_block = self.chain[-DIFFICULTY_ADJUSTMENT_INTERVAL]
            time_taken = self.chain[-1]['timestamp'] - prev_adjustment_block['timestamp']
            target_time = DIFFICULTY_ADJUSTMENT_INTERVAL * BLOCK_TIME_TARGET
            
            if time_taken < target_time / 2:
                return MINING_DIFFICULTY + 1
            elif time_taken > target_time * 2:
                return max(1, MINING_DIFFICULTY - 1)
        return MINING_DIFFICULTY

    def start_block_time_monitor(self):
        """Background thread to monitor block times"""
        def monitor():
            while True:
                if len(self.chain) > 1:
                    last_block_time = self.chain[-1]['timestamp']
                    current_time = time.time()
                    time_since_last_block = current_time - last_block_time
                    self.block_time_history.append(time_since_last_block)
                    if len(self.block_time_history) > 100:
                        self.block_time_history.pop(0)
                time.sleep(10)
        
        thread = threading.Thread(target=monitor)
        thread.daemon = True
        thread.start()

    def get_current_mining_reward(self):
        """Bitcoin-like halving mechanism"""
        halvings = len(self.chain) // HALVING_INTERVAL
        return max(1, INITIAL_MINER_REWARD // (2 ** halvings))

    def visualize_blockchain(self):
        """Enhanced visualization with transaction flow"""
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.network_graph, k=0.15, iterations=50)
        
        # Draw nodes with different colors
        node_colors = []
        for node in self.network_graph.nodes():
            if node == self.node_id:
                node_colors.append('red')  # Current node
            elif node == MINING_SENDER:
                node_colors.append('gold')  # Mining rewards
            else:
                node_colors.append('skyblue')  # Regular nodes
                
        nx.draw(self.network_graph, pos, with_labels=True, node_size=1200, 
                node_color=node_colors, font_size=8, edge_color='gray', width=0.5)
        
        # Add block information
        plt.title(f"Blockchain Network (Block Height: {len(self.chain)})\n"
                 f"Current Mining Reward: {self.get_current_mining_reward()} coins\n"
                 f"Difficulty: {self.calculate_difficulty()} leading zeros",
                 fontsize=10)
        
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=150)
        img.seek(0)
        plt.close()
        return base64.b64encode(img.getvalue()).decode()

    def create_wallet(self):
        """HD wallet creation with security features"""
        private_key = SigningKey.generate(curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        wallet_address = public_key.to_string().hex()
        
        creation_time = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        wallet_id = hashlib.sha256(wallet_address.encode()).hexdigest()[:8]
        
        self.wallets[wallet_address] = INITIAL_BALANCE
        return {
            "wallet_address": wallet_address,
            "wallet_id": wallet_id,
            "private_key": private_key.to_string().hex(),
            "creation_time": creation_time,
            "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={wallet_address}",
            "security_notes": [
                "Never share your private key",
                "Backup your wallet securely",
                "This wallet is deterministic and can be recreated from the private key"
            ]
        }

    def submit_transaction(self, sender_address, recipient_address, value, signature, memo=None, fee=0.1, contract_id=None):
        """Enhanced transaction processing"""
        total_amount = value + fee
        
        transaction = {
            'txid': hashlib.sha256(f"{sender_address}{recipient_address}{value}{time.time()}".encode()).hexdigest(),
            'sender_address': sender_address,
            'recipient_address': recipient_address,
            'value': value,
            'fee': fee,
            'memo': memo,
            'contract_id': contract_id,
            'timestamp': time.time(),
            'status': 'pending'
        }
        
        # Skip signature verification for mining rewards
        if sender_address != MINING_SENDER:
            if not self.verify_transaction_signature(sender_address, signature, transaction):
                transaction['status'] = 'invalid_signature'
                return False
                
        if self.wallets.get(sender_address, 0) < total_amount:
            transaction['status'] = 'insufficient_funds'
            return False
            
        if contract_id and contract_id in self.smart_contracts:
            if not self.execute_contract(contract_id, transaction):
                transaction['status'] = 'contract_execution_failed'
                return False

        self.wallets[sender_address] -= total_amount
        self.wallets[recipient_address] += value
        self.wallets[MINING_SENDER] += fee
        
        transaction['status'] = 'confirmed'
        self.transactions.append(transaction)
        self.transaction_history[sender_address].append(transaction)
        self.transaction_history[recipient_address].append(transaction)
        
        if sender_address != MINING_SENDER:
            self.network_graph.add_edge(sender_address, recipient_address)
        
        return len(self.chain) + 1

    def create_block(self, nonce, previous_hash):
        """Enhanced block creation with metadata"""
        block = {
            'block_number': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.transactions,
            'nonce': nonce,
            'previous_hash': previous_hash,
            'miner': self.node_id,
            'merkle_root': self.calculate_merkle_root(),
            'difficulty': self.calculate_difficulty(),
            'reward': self.get_current_mining_reward(),
            'version': '1.2.0',
            'size': len(json.dumps(self.transactions).encode()),
            'transaction_count': len(self.transactions)
        }
        
        self.transactions = []
        self.chain.append(block)
        return block

    def proof_of_work(self):
        """Mining with dynamic difficulty"""
        current_difficulty = self.calculate_difficulty()
        nonce = 0
        print(f"Mining started at difficulty {current_difficulty}...")
        
        while not self.valid_proof(self.transactions, self.chain[-1]['previous_hash'], nonce, current_difficulty):
            nonce += 1
            if nonce % 100000 == 0:
                print(f"Attempted {nonce} nonces...")
        return nonce

    def valid_proof(self, transactions, last_hash, nonce, difficulty):
        """Proof validation"""
        guess = f"{transactions}{last_hash}{nonce}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == '0' * difficulty

    def get_stats(self):
        """Comprehensive blockchain statistics"""
        return {
            'block_height': len(self.chain),
            'transaction_count': sum(len(block['transactions']) for block in self.chain),
            'wallet_count': len(self.wallets),
            'network_nodes': len(self.nodes),
            'mining_difficulty': self.calculate_difficulty(),
            'current_reward': self.get_current_mining_reward(),
            'average_block_time': sum(self.block_time_history)/len(self.block_time_history) if self.block_time_history else 0,
            'total_supply': INITIAL_BALANCE * len(self.wallets) + sum(block['reward'] for block in self.chain)
        }

# Initialize Flask and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Create blockchain instance
blockchain = Blockchain()

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    emit('chain_update', {'chain': blockchain.chain})
    emit('network_update', {'graph': blockchain.visualize_blockchain()})
    emit('stats_update', blockchain.get_stats())

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    return jsonify(blockchain.create_wallet()), 200

@app.route('/wallet/balance/<wallet_address>', methods=['GET'])
def get_balance(wallet_address):
    balance = blockchain.wallets.get(wallet_address, 0)
    return jsonify({
        'wallet_address': wallet_address,
        'balance': balance,
        'unconfirmed_balance': balance
    }), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.json
    required = ['sender_address', 'recipient_address', 'value', 'signature']
    if not all(k in values for k in required):
        return jsonify({'error': 'Missing values'}), 400
    
    memo = values.get('memo', '')
    fee = values.get('fee', 0.1)
    
    transaction_result = blockchain.submit_transaction(
        values['sender_address'],
        values['recipient_address'],
        values['value'],
        values['signature'],
        memo,
        fee,
        values.get('contract_id')
    )
    
    if transaction_result is False:
        return jsonify({'message': 'Invalid Transaction!'}), 406
        
    socketio.emit('transaction_update', {'transactions': blockchain.transactions})
    socketio.emit('network_update', {'graph': blockchain.visualize_blockchain()})
    socketio.emit('stats_update', blockchain.get_stats())
    
    return jsonify({
        'message': f'Transaction will be added to Block {transaction_result}',
        'txid': blockchain.transactions[-1]['txid']
    }), 201

@app.route('/blockchain/visualize', methods=['GET'])
def visualize():
    return jsonify({'image': blockchain.visualize_blockchain()}), 200

@app.route('/blockchain/stats', methods=['GET'])
def get_stats():
    return jsonify(blockchain.get_stats()), 200

@app.route('/mine', methods=['GET'])
def mine():
    start_time = time.time()
    nonce = blockchain.proof_of_work()
    mining_time = time.time() - start_time
    
    blockchain.submit_transaction(
        sender_address=MINING_SENDER,
        recipient_address=blockchain.node_id,
        value=blockchain.get_current_mining_reward(),
        signature=""
    )
    
    previous_hash = hashlib.sha256(json.dumps(blockchain.chain[-1]).encode()).hexdigest()
    block = blockchain.create_block(nonce, previous_hash)
    
    socketio.emit('block_mined', {
        'block': block,
        'mining_time': mining_time
    })
    socketio.emit('network_update', {'graph': blockchain.visualize_blockchain()})
    socketio.emit('stats_update', blockchain.get_stats())
    
    return jsonify({
        'message': "New Block Forged",
        'block': block,
        'mining_time': f"{mining_time:.2f} seconds",
        'miner': blockchain.node_id
    }), 200

if __name__ == '__main__':
    print("""
    ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗ ██████╗ ██╗  ██╗
    ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝ ██║ ██╔╝
    ██████╔╝██║     ██║   ██║██║     █████╔╝ ██║  ███╗█████╔╝ 
    ██╔══██╗██║     ██║   ██║██║     ██╔═██╗ ██║   ██║██╔═██╗ 
    ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗╚██████╔╝██║  ██╗
    ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
    """)
    print(f"Starting blockchain node: {blockchain.node_id}")
    print(f"Initial mining reward: {blockchain.get_current_mining_reward()} coins")
    print(f"Initial difficulty: {blockchain.calculate_difficulty()} leading zeros")
    if __name__ == '__main__':
     socketio.run(
        app,
        host='0.0.0.0',  # ← MUST be 0.0.0.0 (not 127.0.0.1)
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True,
        use_reloader=False  # ← Prevents double ports in Docker
    )