# Things to remember during test creation

- test duplication of registrationID or atleast incorporate it in a test
- test error checking when a client sends a message to itself
- Empty message queue before new messages are sent, the queue stores messages which should have been sent when the service was down 
- Try to send message to disconnected client. Should receive messages upon reconnection (registering again)
- Try to send to someone who has never registered. What should happen?

# Queue for sending to disconnected client
- Server: when `success` returned `False`, that means recipient is disconnected. Store `sender`, `recipient` and `message` in queue.
- Server: when `recipient` from earlier case registers again, empty queue for that `recipient`.

# Message status for groups
- `TODO`: Change logs to `Sent <message>`
- `TODO`: Change logs to `Delivered <message> to <recipient>`

# Testing
- Figure out a way to start routing server and accept connections
- Start clients
- send commands from client
- get received response