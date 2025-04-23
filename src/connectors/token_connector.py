import os
import sys
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL         = "https://ethereum-sepolia-rpc.publicnode.com"
CONTRACT_ADDR   = "0xc9Cf4D74BF240B26ae1b613f85696eE8DA0aD549"
USER_ADDRESS    = "0xf92769A0dFee5B4807daC7De454a0AE009886Fb0"

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
    print(f"balanceOf({user}) = {w3.from_wei(raw,'ether')} MMM")

def get_price():
    raw = contract.functions.getPrice().call()
    print(f"getPrice() = {w3.from_wei(raw,'ether')} USDT / MMM")

def get_usdt():
    addr = contract.functions.usdt().call()
    print(f"usdt() = {addr}")

def get_treasury():
    addr = contract.functions.treasury().call()
    print(f"treasury() = {addr}")

def get_total_stable():
    raw = contract.functions.totalStable().call()
    print(f"totalStable() = {w3.from_wei(raw,'ether')} USDT")

def get_total_borrow():
    raw = contract.functions.totalBorrowMMM().call()
    print(f"totalBorrowMMM() = {w3.from_wei(raw,'ether')} MMM")

# Like CLI
USAGE = """
Usage: python token_cli.py <command>

Commands:
  balance — show balanceOf(USER_ADDRESS)
price — call getPrice()
usdt — call usdt()
treasury     — call treasury()
totalStable — call totalStable()
totalBorrow — call totalBorrowMMM()
"""

def main():
    if len(sys.argv) < 2:
        print(USAGE); sys.exit(1)
    cmd = sys.argv[1].lower()
    if cmd == "balance":
        if not USER_ADDRESS:
            print("❌ Please set USER_ADDRESS in .env")
            sys.exit(1)
        get_balance(USER_ADDRESS)
    elif cmd == "price":
        get_price()
    elif cmd == "usdt":
        get_usdt()
    elif cmd == "treasury":
        get_treasury()
    elif cmd == "totalstable":
        get_total_stable()
    elif cmd == "totalborrow":
        get_total_borrow()
    else:
        print("❌ Unknown command\n", USAGE)
        sys.exit(1)

if __name__ == "__main__":
    main()