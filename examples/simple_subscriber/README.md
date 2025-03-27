## Sample Subscriber Agent
Run this agent with `poetry run python main.py` command after installing the SDK dependencies.

## How to get a access token
In order to get an access token, you have multiple options:

1. As a user you should create an API Key from the UI. Once created, you treat this as the refresh token. You should attenuate the biscuit with a expire_at timestamp (maximum of 10 minutes for now), and then you will have an access token.

2. As an agent you should first create an agent authentication biscuit (Agent.authentication_biscuit), then you can use ProtocolClient.get_biscuit to get the biscuit, which can be used as the access token.