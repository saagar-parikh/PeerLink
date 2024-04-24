import socket
import json
import time
from _thread import *
import argparse
from datetime import datetime
from pycentraldispatch import PyCentralDispatch
from CustomLog import *
from commands import *

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost", help="Host IP address")
parser.add_argument("--port", type=int, default=8008, help="Port number")

args = parser.parse_args()


HOST = args.host
PORT = args.port

state = 0.0  # state should always be a float


# instantiate serialized dispatcher
global_queue = PyCentralDispatch.global_queue()

server = Server()


def client_handler(connection, address):
    global server
    # Receive data from client
    try:
        payload = json.loads(connection.recv(2048).decode("utf-8"))
    except socket.error as e:
        logger.error("[ERROR] Cannot receive " + str(e))
        connection.close()
        return
    except Exception as e:
        logger.error("[ERROR] " + str(e))
        connection.close()
        return

    command = payload["command"]
    if command == "REGISTER":
        server.register_client(payload, address)
    elif command == "SEND_MSG":
        server.send_msg(payload)
    elif command == "CREATE_GROUP":
        server.create_group(payload)
    elif command == "JOIN_GROUP":
        server.join_group(payload)
    elif command == "LEAVE_GROUP":
        server.leave_group(payload)
    else:
        # TODO: Invalid command
        pass

    connection.close()


def accept_connections(ServerSocket):
    client, address = ServerSocket.accept()
    # logger.info("Connected to: " + address[0] + ":" + str(address[1]))
    global_queue.dispatch_sync(client_handler, args=(client, address))
    # start_new_thread(client_handler, (client, address))


def main():
    # Create a socket and bind to a port. SO_REUSEADDR=1 for reusing address
    ServerSocket = socket.socket()
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        ServerSocket.bind((HOST, PORT))
    except socket.error as e:
        logger.error(str(e))

    while True:
        ServerSocket.listen()
        print("Server is listening on the port {}".format(PORT))
        try:
            accept_connections(ServerSocket)
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt")
            break


if __name__ == "__main__":
    main()
