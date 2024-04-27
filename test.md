# Things to remember during test creation

- test duplication of registrationID or atleast incorporate it in a test
- test error checking when a client sends a message to itself
- Empty message queue before new messages are sent, the queue stores messages which should have been sent when the service was down 
- Try to send message to disconnected client. Should receive messages upon reconnection (registering again). ONLY if personal message, not group
- Try to send to someone who has never registered. What should happen?
- for any invalid command, delivered log shouldn't be printed

# Queue for sending to disconnected client
- Server: when `success` returned `False`, that means recipient is disconnected. Store `sender`, `recipient` and `message` in queue.
- Server: when `recipient` from earlier case registers again, empty queue for that `recipient`.

# Message status for groups
- Change logs to `Sent <message>`
- Change logs to `Delivered <message> to <recipient>`

# Testing
- Figure out a way to start routing server and accept connections
- Start clients
- send commands from client
- get received response

# Replication Manager
- Start heartbeating to all servers, primary as well as backup
- When primary server failure detected, choose backup to become primary and communicate it to that server
- Send message to all clients sharing the new address of the new primary
- TODO: bring old server back up automatically
- Failure scenario: Server dies after receiving heartbeat but before acknowledging. We haven't implemented timeout so RM will just get stuck
- TODO: When primary comes back up, consider as backup automatically


Test 1

Start server
Start client
Send Register message
Test expect response: <correct-response>

Test 2
Start server
Start client
Send Send_msg
Expected response: failure, send register first

