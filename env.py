import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="emergency_ai\BlockChain\.env")

# Load variables from .env file if present

def getPrivateKey():
    return os.getenv("PRIVATE_KEY")

#print(f"Private Key: {getPrivateKey()}")
