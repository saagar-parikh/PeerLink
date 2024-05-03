import socket
import json
import time
from _thread import *
import argparse
from datetime import datetime
from pycentraldispatch import PyCentralDispatch
from CustomLog import *
from commands import *
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost", help="Host IP address")
parser.add_argument("--port", type=int, default=8008, help="Port number")
parser.add_argument("--backup", action="store_true", help="Primary server")

args = parser.parse_args()


HOST = args.host
PORT = args.port

state = 0.0  # state should always be a float


# instantiate serialized dispatcher
global_queue = PyCentralDispatch.global_queue()

server = Server()


HOST_LIST = [("localhost", 8008), ("localhost", 8009)]
CHECKPOINT_INTERVAL = 1
backup = args.backup


def send_ckpt_msg(host, port):
    """
    method to periodically send checkpoint state by serializing
    the state of the server to the specified address. The method
    returns true if the checkpoint message is sent successfully
    or it returns false

    host: IP address of the recipient
    port: port number of the recipient
    """
    global server

    checkpoint = server.to_json()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        # print(f"Connected to server {host_list[ind][0]}:{host_list[ind][1]}")
    except socket.error as e:
        logger.error(f"Trying to connect to server {host}:{port}, Error: {str(e)}")

    try:
        # Send data
        sock.send(checkpoint.encode("utf-8"))

        logger.send(f"Sent checkpoint to {host}:{port}")

        # # Receive data from the server
        # received = json.loads(sock.recv(1024).decode("utf-8"))

    except socket.error as e:
        logger.error(f"Server {host}:{port} is down " + str(e))
        return False
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt")
        return False
    except Exception as e:
        logger.error("[ERROR] " + str(e))
        return False

    return True


def send_ckpt_msg_to_all():
    """
    wrapper over the send_ckpt_msg to send
    checkpoints to all the backup servers
    """
    global HOST_LIST
    for host, port in HOST_LIST:
        if (host, port) != (HOST, PORT):  # if not myself
            send_ckpt_msg(host, port)


def send_ckpts():
    """
    method to periodically send checkpoints
    """
    while True:
        time.sleep(CHECKPOINT_INTERVAL)
        send_ckpt_msg_to_all()


def accept_ckpts(connection, address):
    """
    method for handling incoming checkpoint messages from other
    servers. The checkpoint messages are deserialized and checked 
    if it is a heartbeat or primary update to handle it appropriately
    The checkpoint messages in this case are a proxy for heartbeats

    connection: sender's socket object
    address: tuple representing senders address 
    """
    global server
    global backup
    # Receive data from client
    try:
        checkpoint = json.loads(connection.recv(2048).decode("utf-8"))
    except socket.error as e:
        logger.error("[ERROR] Cannot receive " + str(e))
        connection.close()
        return
    except Exception as e:
        logger.error("[ERROR] " + str(e))
        connection.close()
        return

    if "command" in checkpoint.keys():
        if checkpoint["command"] == "HEARTBEAT":
            start_new_thread(
                accept_heartbeats, (connection, address, checkpoint["command"])
            )
            # connection.close()
            return
        elif checkpoint["command"] == "UPDATE_PRIMARY":
            print("Primary server changed")
            sys.stdout.flush()
            backup = False
            connection.close()
            return

    # Update state
    server = Server.from_json(checkpoint)
    logger.info("Updated state from checkpoint")
    print("Checkpoint received")
    sys.stdout.flush()

    # print all clients
    for client_id, client in server.client_addr.items():
        logger.info(f"Client ID: {client_id}, Client: {client}")

    connection.close()


def client_handler(connection, address):
    """
    The client handler handles client requests by
    deserializing the payload and calling the appropriate 
    functions defined to handle the sent commands

    The supported commands are:
    REGISTER
    SEND_MSG <RECV> <MSG>
    CREATE_GROUP <NAME>
    JOIN_GROUP <NAME>
    LEAVE_GROUP <NAME>

    connection: socket object representing sender's connection
    address: tuple representing sender's address
    """
    global server
    # Receive data from client
    try:
        payload = json.loads(connection.recv(2048).decode("utf-8"))
        logger.receive(f"Received from {address[0]}:{address[1]}")
    except socket.error as e:
        logger.error("[ERROR] Cannot receive " + str(e))
        connection.close()
        return
    except Exception as e:
        logger.error("[ERROR] " + str(e))
        connection.close()
        return

    command = payload["command"]
    if command == "HEARTBEAT":
        start_new_thread(accept_heartbeats, (connection, address, command))
        return
    if command == "REGISTER":
        success = server.register_client(payload, address)
        if success[payload["sender"]]:
            print(f"Client {payload['sender']} registered successfully")
            sys.stdout.flush()
    elif command == "SEND_MSG":
        success = server.send_msg_command(payload)
        # for k, v in success.items():
        #     if v:
        #         print(f"{payload['sender']} : {payload['message']}")
    elif command == "CREATE_GROUP":
        success = server.create_group(payload)
        for k, v in success.items():
            if v:
                print(f"Group {payload['message']} created successfully")
                sys.stdout.flush()
    elif command == "JOIN_GROUP":
        success = server.join_group(payload)
    elif command == "LEAVE_GROUP":
        success = server.leave_group(payload)
    else:
        success = {payload["recipient"]: False}

    # success is a dict with ID: (True or False)

    # Send response to client
    send_payload = {"success": success}
    try:
        connection.send(json.dumps(send_payload).encode("utf-8"))
    except socket.error as e:
        logger.error("[ERROR] Cannot send " + str(e))
        connection.close()
    except Exception as e:
        logger.error("[ERROR] " + str(e))

    connection.close()


def accept_heartbeats(connection, address, command):
    """
    helper function to send acknowledgements to received
    heartbeat messages

    connection: socket object representing the sender
    address: tuple representing the sender's address
    command: command received (eg. HEARTBEAT)
    """

    # Receive data from rm
    logger.info("Start accept heartbeats")
    if command == "HEARTBEAT":
        success = True
    else:
        success = False

    # Send response to client
    send_payload = {"success": success}
    try:
        connection.send(json.dumps(send_payload).encode("utf-8"))
    except socket.error as e:
        logger.error("[ERROR] Cannot send " + str(e))
        connection.close()
    except Exception as e:
        logger.error("[ERROR] " + str(e))

    logger.send("Sent heartbeat ack to " + str(address))

    connection.close()


def accept_connections(ServerSocket, target_func=client_handler):
    """
    helper function to accept incoming connections and
    call the appropriate client handler

    ServerSocket: server socket object representing the listening socket
    target_func: The function to handle incoming connections (client_handler) 
    """
    client, address = ServerSocket.accept()

    # logger.info("Connected to: " + address[0] + ":" + str(address[1]))
    global_queue.dispatch_sync(target_func, args=(client, address))
    # start_new_thread(client_handler, (client, address))


def main_primary(ServerSocket):
    """
    main function which periodically sends checkpoints to 
    backup servers, while continually listening for incoming 
    connections and dispatching them appropriately using the 
    accept_connection method

    serversocket: socket object representing the primary
    server's listening socket
    """
    start_new_thread(send_ckpts, ())

    logger.info("Server is listening on the port {}".format(PORT))
    while True:
        logger.info("Waiting to listen")
        ServerSocket.listen()
        logger.info("Done listening")
        # sys.stdout.flush()
        try:
            accept_connections(ServerSocket)
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt")
            break


def main_backup(ServerSocket):
    """
    function for backup server's operation, if the backup is
    promoted to main_primary it invokes main_primary method
    otherwise it continues to listen to incoming checkpoint
    messages and client connections and dispatches them to
    the appropriate handler

    serversocket: socket object representing the primary
    server's listening socket
    """
    global backup

    # Create a socket and bind to a port. SO_REUSEADDR=1 for reusing address
    # ServerSocket = socket.socket()
    # ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # try:
    #     ServerSocket.bind((HOST, PORT))
    # except socket.error as e:
    #     logger.error(str(e))

    logger.info("Server is listening on the port {}".format(PORT))
    while True:
        ServerSocket.listen()
        try:
            accept_connections(ServerSocket, target_func=accept_ckpts)
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt")
            break
        if not backup:
            logger.warn("Exiting main_backup, changing to main_primary")
            print("Exiting backup, changing to primary")
            sys.stdout.flush()
            main_primary(ServerSocket)
            return


if __name__ == "__main__":
    # Create a socket and bind to a port. SO_REUSEADDR=1 for reusing address
    ServerSocket = socket.socket()
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        ServerSocket.bind((HOST, PORT))
    except socket.error as e:
        logger.error(str(e))
    if args.backup:
        main_backup(ServerSocket)
    else:
        main_primary(ServerSocket)
