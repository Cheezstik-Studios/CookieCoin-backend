import hashlib # for hashing
import time 
from flask import Flask, request # to send data over a server
from flask_sock import Sock # a websocket extension for flask
import json # to jsonify
import websocket

# sets up flask and websocket
app = Flask(__name__)
sock = Sock(app)

#defines the Block class
class Block: 
  def __init__(self, index, prevHash, timestamp, data, nonce, target): 
    # a block has an index, the pervious block's hash, a timestamp, transaction data, a nonce (number used once), a target, and a hash calculated from the rest
    self.index = index
    self.prevHash = prevHash
    self.timestamp = timestamp
    self.data = data
    self.nonce = nonce
    self.target = target
    self.hash = self.calculateHash()
  
  def calculateHash(self):
    # uses the sha256 cryptographic hashing algorithm
    return hashlib.sha256(
      (str(self.index) + self.prevHash + str(self.timestamp) + self.data + str(self.nonce)).encode()
    ).hexdigest()
# defines how json.dumps() jsonifies Block objects
class jsonencoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Block):
      return {'__type__': 'Block', 'index': obj.index, 'hash': obj.hash, 'prevHash': obj.prevHash, 'timestamp': obj.timestamp, 'data': obj.data, 'nonce': obj.nonce, 'target': obj.target}
    
    # just in case I later use this on a non-Block
    return super().default(obj)

def jsondecoder(dct):
    if "__type__" in dct:
        if dct["__type__"] == "Block":
            return Block(dct['index'], dct['prevHash'], dct['timestamp'], dct['data'], dct['nonce'], dct['target'])
    return dct

# returns the genesis block
def genesis():
  return Block(0, # zero-indexed
    '0000000000000000000000000000000000000000000000000000000000000000', # just a fully zero pervious hash
    0, # this was made on 1/1/1970 trust me
    'You feel like making cookies. But nobody wants to eat your cookies.', # no transaction data, so I might as well
    67, # SIX SE- sorry
    (2 ** 256 - 1)) 

# initialise the blockchain and peers list
blockchain = [genesis()]
connected_peers = []
expectedTarget = 0

# random utility functions grouped so they get replaced when I change the blockchain storage method
def latestBlock():
  return blockchain[-1]
def getBlockchain():
  return blockchain
def actuallyReplaceChain(newBlockchain):
  blockchain[:] = newBlockchain
def addBlock(block):
  blockchain.append(block)
def getBlock(i):
  return blockchain[i]
def sendLatest():
  for ws, address in connected_peers:
    ws.send(json.dumps({'type': 'sendAll', 'body': getBlockchain()}, cls=jsonencoder))

# self-explanatory
def nextBlock(data, nonce, target):
  prevBlock = latestBlock()
  index = prevBlock.index + 1
  prevHash = prevBlock.hash
  timestamp = int(time.time())
  return Block(index, prevHash, timestamp, data, nonce, target)

# validator functions
def isValidStructure(block):
  return (type(block.index) is int 
    and type(block.prevHash) is str 
    and type(block.hash) is str 
    and type(block.timestamp) is int 
    and type(block.data) is str
    and type(block.nonce) is int
    and type(block.target) is int)
  
def isValidBlock(block, prevBlock):
  if not isValidStructure(block):
    return False
  if prevBlock.index + 1 != block.index:
    return False
  elif prevBlock.hash != block.prevHash:
    return False
  elif block.hash != block.calculateHash():
    return False
  elif not hashIsDifficulty(block.hash, block.target):
    return False
  
  return True

def isValidChain(blockchain):
  if blockchain[0].hash != genesis().hash:
    return False

  for i in range(len(blockchain)-1):
    if not isValidBlock(blockchain[i+1], blockchain[i]):
      return False

  return True
 
# checks if a block has a valid difficulty
def hashIsDifficulty(hash, target):
  if target != expectedTarget:
    latestIndex = latestBlock().index
    block = getBlock(latestIndex // 144 * 144)
    otherBlock getBlock((latestIndex // 144 - 1) * 144)
    oldTarget = otherBlock.target
    timeTaken = block.timestamp - otherBlock.timestamp
    expectedTarget = oldTarget * (timeTaken / 86400)
    if target != expectedTarget:
      return False
  number = int(hash, 16)
  return number <= target

# replaces the chain if it's valid and broadcasts it
def replaceChain(newBlocks):
  if isValidChain(newBlocks) and len(newBlocks) > len(getBlockchain()):
    actuallyReplaceChain(newBlocks)
    sendLatest()

def connect_to_peer(address):
    if len(connected_peers) < 20 and address not in [item[1] for item in connected_peers]:
      ws = websocket.create_connection(
          f"ws://{address}/connect"
      )

      connected_peers.append((ws, address))

@sock.route('/connect')
def connect(ws):
  peer = f'{request.remote_addr}:{request.environ.get("REMOTE_PORT")}'
  if len(connected_peers) >= 20:
    peers = [item[1] for item in connected_peers]
    ws.send(json.dumps({'type': 'sendPeers', 'body': peers}))
    ws.send(json.dumps({'type': 'disconnect'}))
    return
  connected_peers.append((ws, peer))

  try:
    while True:
      data = ws.receive()
      if data is None:
        break
      else:
        data = json.loads(data, object_hook=jsondecoder)
        requestType = data['type']
        match requestType:
          case 'queryLatest':
            ws.send(json.dumps({'type': 'sendLatest', 'body': latestBlock()}, cls=jsonencoder))
          case 'queryAll':
            ws.send(json.dumps({'type': 'sendAll', 'body': getBlockchain()}, cls=jsonencoder))
          case 'sendLatest':
            if data['body']['index'] > latestBlock().index + 1:
              ws.send(json.dumps({'type': 'queryAll'}))
            elif data['body']['index'] <= latestBlock().index:
              ws.send(json.dumps({'type': 'sendLatest', 'body': latestBlock()}, cls=jsonencoder))
            else:
              if isValidBlock(data['body'], latestBlock()):
                addBlock(data['body']) 
          case 'sendAll':
            replaceChain(data['body'])
          case 'queryPeers':
            peers = [item[1] for item in connected_peers]
            ws.send(json.dumps({'type': 'sendPeers', 'body': peers}))
          case 'sendPeers':
            peers = data['body']
            for item in peers:
              connect_to_peer(item)
          case 'disconnect':
            break
  finally:
    connected_peers.remove((ws, peer))
