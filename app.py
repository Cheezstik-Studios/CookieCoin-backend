import hashlib # for hashing
import time 
from flask import Flask, request # to send data over a server
from flask_sock import Sock # a websocket extension for flask
import json # to jsonify

# sets up flask and websocket
app = Flask(__name__)
sock = Sock(app)

#defines the Block class
class Block: 
  def __init__(self, index, hash, prevHash, timestamp, data): 
    # a block has an index, the pervious block's hash, a timestamp, transaction data, and a hash calculated from the rest
    self.index = index
    self.previousHash = prevHash
    self.timestamp = timestamp
    self.data = data
    self.hash = hash

# defines how json.dumps() jsonifies Block objects
class jsonencoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Block):
      return {'index': obj.index, 'hash': obj.hash, 'prevHash': obj.prevHash, 'timestamp': obj.timestamp, 'data': obj.data}
    
    # just in case I later use this on a non-Block
    return super().default(obj)
          
def calculateHash(index, prevHash, timestamp, data):
  # uses the sha256 cryptographic hashing algorithm
  return hashlib.sha256(
    (str(index) + prevHash + str(timestamp) + data).encode()
  ).hexdigest()

# returns the genesis block
def genesis():
  # don't as why that timestamp is being used specifically...
  timestamp = 1000212390
  return Block(0, 
               calculateHash(0, 
                             '0000000000000000000000000000000000000000000000000000000000000000', # just a fully zero hash
                             timestamp, 
                             'You feel like making cookies. But nobody wants to eat your cookies.'), # no transaction data, so i might as well
               '0000000000000000000000000000000000000000000000000000000000000000', 
               timestamp, 
               'You feel like making cookies. But nobody wants to eat your cookies.')

# initialise the blockchain and peers list
blocks = [genesis()]
connected_peers = []

# random utility functions grouped so they get replaced when I change the blockchain storage method
def latestBlock():
  return blocks[-1]
def getBlockchain():
  return blocks
def actuallyReplaceChain(newBlocks):
  blocks[:] = newBlocks

# not yet
def broadcastLatest():
  pass

# self-explanatory
def nextBlock(data):
  prevBlock = latestBlock()
  index = prevBlock.index + 1
  prevHash = prevBlock.hash
  timestamp = int(time.time())
  hash = calculateHash(index, prevHash, timestamp, data)
  return Block(index, hash, prevHash, timestamp, data)

# validator functions
def isValidStructure(block):
  return (type(block.index) is int 
          and type(block.prevHash) is str 
          and type(block.hash) is str 
          and type(block.timestamp) is int 
          and type(block.data) is str)
  
def isValidBlock(block, prevBlock):
  if prevBlock.index + 1 != block.index:
    return False
  elif prevBlock.hash != block.prevHash:
    return False
  elif calculateHash(block.index, block.prevHash, block.timestamp, block.data) != block.hash:
    return False
  
  return True and isValidStructure(block)

def isValidChain(blockchain):
  if blockchain[0] != genesis():
    return False

  for i in range(len(blockchain)-1):
    if not isValidBlock(blockchain[i+1], blockchain[i]):
      return False

  return True

# replaces the chain if it's valid and broadcasts it
def replaceChain(newBlocks):
  if isValidChain(newBlocks) and len(newBlocks) > len(getBlockchain()):
    actuallyReplaceChain(newBlocks)
    broadcastLatest()

@app.route('/blocks')
def blocks():
  return (json.dumps(getBlockchain(), cls=jsonencoder))

@sock.route('/mineblock')
def mineblock(ws):
  newBlock = nextBlock(ws.receive())
  ws.send(json.dumps(newBlock))

@sock.route('/connect')
def connect(ws):
  peer = f'{request.remote_addr}:{request.environ.get("REMOTE_PORT")}'
  connected_peers.append((ws, peer))

  try:
    while True:
      data = ws.receive()
      if data is None:
        break
  finally:
    connected_peers.remove((ws, peer))

@app.route('/peers')
def peers():
  return (json.dumps([item[1] for item in connected_peers]))
