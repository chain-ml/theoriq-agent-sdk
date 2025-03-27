## Sample Subscriber Agent
This agent subscribe to another publisher agent stream.


## How to test
1. Install the dependencies on the publisher agent and run is using the existing scripts.
2. Copy the agent id from the log where it is written in green and starts with "0x".
3. Paste it in the .env file of the subscriber agent under the env variable `PUBLISHER_AGENT_ID`.
4. Run the subscriber agent.