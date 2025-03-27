## Sample Subscriber Agent
This agent subscribe to another publisher agent stream.


## How to test
1. Install the dependencies on the publisher agent and run is using the existing scripts.
2. Copy the agent id from the log where it is written in green and starts with "0x".
3. Paste it in the .env file of the subscriber agent under the env variable `PUBLISHER_AGENT_ID`.
4. Run the subscriber agent.
5. Run the following CURL so that the publisher agent publishes an event:
```
curl --location '[publisher agent address]/publish' \
--header 'Content-Type: application/json' \
--header 'Authorization: [Authorization biscuit]' \
--data '{"data":"Your data"}'
```
# Note: You should get [Authorization biscuit], and [publisher agent address] in this curl.
# Note2: Please be mindful that both these agents should be registered by the BE instance you are working otherwise, they will throw error.