from theoriq.biscuit import get_new_key_pair

if __name__ == "__main__":
    public_key, private_key = get_new_key_pair()
    print(f"AGENT_PRIVATE_KEY = {private_key}")
    print(f"Corresponding public key: `{public_key}`")
