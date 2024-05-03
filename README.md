# PeerLink

PeerLink is a distribted application for peer to peer messaging between multiple clients over a network. The system supports real-time communication among peers and also supports group semantics. A peer can join a group and automatically subscribes to all the messages in the group from the other group participants. PeerLink allows for sending messages to disconnected peers ensuring that sent messages are delivered eventually when the peer rejoins the network and message states are used to determine the status of the sent messages. Fault tolerance in PeerLink is handled through passive replication and checkpointing. On failure of the primary one of the backup servers which is up to date with the primary's state through checkpoints is promoted and the system continues to operate despite failures.


Each peer communicates through a router in order to send and receive messages, the router is used for managing metadata and acts as a mediator helping in connection management and message routing. Clients register with the server by providing a unique identifier (ID). Client registration allows the server to manage client connections and facilitate message routing and discovery.Clients can send messages directly to other clients using their unique IDs. The router routes messages between sender and recipient clients, ensuring secure and reliable communication channels. Peer-to-peer messaging allows users to exchange private messages in real-time.

The system also supports group semantics, clients can join one or more groups. Whenever a client joins a group, every client message will be broadcast to all the members of the group and at the same time the client subscribes to all the messages sent by other participants in the group. The system tracks the state of each message, including "Sent" and "Delivered". When a client sends a message, the server marks it as "Sent" and routes it to the recipients. Upon successful delivery, the server updates the message state to "Delivered", and the recipients receive notifications. Message state tracking ensures message delivery reliability and provides transparency to users about the status of their messages.

The system supports passive replication as a mechanism to deal with failures of the routing server. In case of primary server failure, a backup server takes over to maintain service continuity. Primary server failure in this system is detected through heartbeats and the state of the system is periodically saved using checkpoints and in some sense, checkpoints in the system serve as a proxy for heartbeats. This method allows seamless transition when the primary node fails ensuring one of the backup servers can take over without any data loss.



## Clients

To open new clients, run following commands in separate terminals
```python
python Client/client.py --ID peer1 --port 8000
python Client/client.py --ID peer2 --port 8001
python Client/client.py --ID peer3 --port 8002
```

## Server

To start server and backups, run following commands in separate terminals
```python
python Server/server.py --port 8008
python Server/server.py --port 8009 --backup
python rm.py
```

## Supported commands

- REGISTER
    - Command for registering the client with the router
- SEND_MSG {receiver} {message_contents}
    - Command to send a message to another peer
- CREATE_GROUP {group_name}
    - Command to greate a group, the client creating the group is automatically a member
- JOIN_GROUP {group_name}
    - Command for a peer to join a group
- LEAVE_GROUP {group_name}
    - command for a peer to leave a group
