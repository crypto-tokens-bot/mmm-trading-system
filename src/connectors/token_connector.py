import sys
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL         = "https://ethereum-sepolia-rpc.publicnode.com"
CONTRACT_ADDR   = "0xc9Cf4D74BF240B26ae1b613f85696eE8DA0aD549"
# USER_ADDRESS    = "0xf92769A0dFee5B4807daC7De454a0AE009886Fb0"

if not RPC_URL or not CONTRACT_ADDR:
    print("❌ Please set RPC_URL and CONTRACT_ADDRESS in your .env")
    sys.exit(1)

# ABI
ABI = [
    {
      "constant": True,
      "inputs": [{"name": "","type": "address"}],
      "name": "balanceOf",
      "outputs": [{"name":"","type":"uint256"}],
      "type": "function"
    },
    {"constant": True,"inputs": [],"name": "getPrice","outputs": [{"name":"","type":"uint256"}],"type": "function"},
    {"constant": True,"inputs": [],"name": "usdt","outputs": [{"name":"","type":"address"}],"type": "function"},
    {"constant": True,"inputs": [],"name": "treasury","outputs": [{"name":"","type":"address"}],"type": "function"},
    {"constant": True,"inputs": [],"name": "totalStable","outputs": [{"name":"","type":"uint256"}],"type": "function"},
    {"constant": True,"inputs": [],"name": "totalBorrowMMM","outputs": [{"name":"","type":"uint256"}],"type": "function"},
]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(Web3.to_checksum_address(CONTRACT_ADDR), abi=ABI)

def get_balance(user: str):
    raw = contract.functions.balanceOf(Web3.to_checksum_address(user)).call()
    return w3.from_wei(raw,'ether')

def get_price():
    raw = contract.functions.getPrice().call()
    return w3.from_wei(raw,'ether')