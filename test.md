# Test Suite for PeerLink

This file documents all the automated test created to test our system, our tests check all the features supported by our implementation like, peer to peer communication, group semantics, group communication, message states and transitions, peer and group messaging during disconnection and reconnection of peers, server failures, etc.

The following tests have been created to test our implementation:
 - Test_Register - 20pt
 - Test_SendMessage - 20pt
 - Test_GroupMsg - 40pt
 - Test_MsgStates - 30pt
 - Test_Disconnection - 20pt
 - Test_Reconnection - 30pt
 - Test_Replication - 40pt

 ----

### Test_Register ###
Checks if a client can successfully register with the server.
The test creates multiple clients and successfuly verifies that they are able to register using the REGISTER command
The overall flow of the test is as follows:
- Check peer1: Registers peer1 and verifies successful registration message from the server.
- Check peer2: Registers peer2 and verifies successful registration message from the server.


### Test_SendMessage ###
This test checks the peer to peer messaging feature of the system by creating multiple clients
and sending messages to and fro among these clients and verifies delivery of these messages
The overall flow of the test is as follows:
- Register multiple clients
- Send message from one registered client to another and verify the delivery of the message
- Send messages from multiple clients to the same recepient and verify the delivery of these messages in FIFO order

### Test_GroupMsg ###
Test to check the group feature supported by the system, where multiple clients can join groups and subscribe to all the messages sent in the group by the participants.

- Register all the clients needed for the test
- Client 1 creates a group
- Add client 2 and client 3 to the created group
- Send messages on the group and verify delivery to the group participants other than the sending participant
- Remove a participant from the group to verify group message semantics and check this client doesn't get subsequent messages
- Rejoin the removed client to the group and verify delivery of messages
- Create multiple groups with overlapping participants to check correct delivery of messages
- Since the same participant is part of multiple groups, a sent message should be delivered to multiple groups


### Test_MsgStates ###
This test check the various supported states of messages and check that they are updated accordingly. Messages sent by peers can be in the "sent" state when they are not delivered to the recepient and the message state updates accordingly on delivery to the recipient.
- Register all the required clients for the test
- Send messages from one peer to another and induce some delays to check the transition of states
- Create a group and check the message state transitions from "sent" to "delivered" even when sent to multiple peers part of a   group
    
### Test_Disconnection ###
This test checks the behaviour of the system when messages are sent to peer who are currently offline or disconnected.
- Register all the required clients for the test
- check peer to peer communication and check initial message states and transitions are as expected
- Disconnect one of the peers and try sending messages to the disconnected peer
- The message state should be set to "sent" and not "delivered"
- The above semantics should also apply to groups
- Create a group and register multiple clients to the group and check messages sent to the group have correct message states
- One of the participants of the group is disconnected and the resulting message state should be "delivered" to the connected clients and "sent" to the disconnected client

### Test_Reconnection ###
This test is an integration test by combining the features of disconnection and reconnection, it checks for the behaviour of the system when messages are sent to disconnected clients and later reconnected, the test also check this on groups
- Register the clients required for the test
- Check peer to peer communication works as expected and message state transition between connected clients is correct
- Disconnect one of the clients and check the message state transition
- Reconnect the disconnected client and check the message is eventually delivered and the message state is updated to "delivered"
- Create a group and register multiple peer in the group and check group messaging sematics works as expected
- Disconnect one of the peers in the group and check the transition of states when messages are sent to the group
- Finally rejoin the disconnected peer and check all the messages eventually reach the disconnected peer and the message state for these messages is set to "delivered" for the peer sending the messages

### Test_Replication ###
Tests the server replication and failover functionality. The test checks if the checkpointing functionality is working as expected and the backup server is promoted when the primary fails.
- Register all the clients required for the test
- Simulate activity between clients before primary failure
- Disconnect the primary server
- Check the backup takesover when primary failure is detected
- Check if system has reached a stable state by simulating client activity and checking for correctness
