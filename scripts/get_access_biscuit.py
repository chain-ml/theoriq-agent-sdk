from datetime import datetime, timezone
from pprint import pprint

import httpx
from biscuit_auth import Biscuit, BlockBuilder, KeyPair, PrivateKey, PublicKey


def cyan(text):
    # ANSI escape code for light grey text
    CYAN = "\033[0;36m"  # Light grey text
    RESET = "\033[0m"
    return f"{CYAN}{text}{RESET}"


def ask_user_input(prompt, default=None):
    """Ask for user input with a default value."""
    user_input = input(cyan(f"{prompt} [{default}]: ")).strip()
    return user_input if user_input else default


# Get the public key from the input
public_key_raw = ask_user_input(
    "Enter the public key (get from the api, for instance: https://theoriq-backend.dev-02.lab.chainml.net/api/v1alpha2/auth/biscuits/public-key)",
    "0x3363f11284bc2671356a847312dfe4e323f8e82e2032fe69e7e079ff3d1c86bf",
)
public_key = PublicKey.from_hex(public_key_raw.removeprefix("0x"))

biscuit_raw = ask_user_input("Enter the API Key")
if not biscuit_raw:
    raise ValueError("API Key is required")
token: Biscuit = Biscuit.from_base64(biscuit_raw, public_key)

expiry_timestamp = ask_user_input(
    "Enter the expiry timestamp (in seconds)", int(datetime.now(timezone.utc).timestamp()) + 3600
)
block_builder = BlockBuilder(f"theoriq:expires_at({expiry_timestamp})")

agent_private_key_raw = ask_user_input("Enter the agent/third party application private key")

agent_private_key = PrivateKey.from_hex(agent_private_key_raw.removeprefix("0x")) if agent_private_key_raw else None

agent_kp = KeyPair.from_private_key(agent_private_key) if agent_private_key else KeyPair()

attenuated_biscuit = token.append(block_builder)

base_api_url = ask_user_input("Enter the base API URL", "https://theoriq-backend.dev-02.lab.chainml.net/api/v1alpha2")
# Get the access token
access_token_url = f"{base_api_url}/auth/api-keys/exchange"
response = httpx.post(access_token_url, headers={"Authorization": f"Bearer {attenuated_biscuit.to_base64()}"})

pprint(response.json())
