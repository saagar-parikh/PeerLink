from datetime import datetime
import socket
import argparse
import json
import time
import string
import random
import threading
from CustomLog import *
from pycentraldispatch import PyCentralDispatch
import threading
from _thread import *

parser = argparse.ArgumentParser()
parser.add_argument("--ID", type=str, required=True, help="Client ID")
parser.add_argument("--port", type=int, required=True, help="Client port")
parser.add_argument("--router_port", type=int, default=8008, help="Router port")
args = parser.parse_args()

ID = args.ID
HOST = "localhost"
PORT = args.port
ROUTER_HOST = "localhost"
ROUTER_PORT = args.router_port

# instantiate serialized dispatcher
global_queue = PyCentralDispatch.global_queue()


def send_msg(client_payload, host, port):

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        # print(f"Connected to server {host_list[ind][0]}:{host_list[ind][1]}")
    except socket.error as e:
        logger.error(f"Trying to connect to server {host}:{port}, Error: {str(e)}")

    try:
        # Server ID is hardcoded to 1 for now
        # Send data
        sock.send(json.dumps(client_payload).encode("utf-8"))

        logger.send("Sent", client_payload)

        # # Receive data from the server
        # received = json.loads(sock.recv(1024).decode("utf-8"))

    except socket.error as e:
        logger.error("Server is down " + str(e))
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt")
    except Exception as e:
        logger.error("[ERROR] " + str(e))


def message_sender():
    while True:
        inp = input()

        inputs = inp.split(" ")
        command = inputs[0]

        if command == "REGISTER":
            recipient = ""
            message = ID
        elif command == "SEND_MSG":
            recipient = inputs[1]
            message = "".join(inputs[2:])
        else:
            recipient = ""
            message = " ".join(inputs[1:])

        # Send message to router
        client_payload = {
            "command": command,
            "sender": ID,
            "recipient": recipient,
            "message": message,  # group name
            "port": PORT,
        }

        start_new_thread(send_msg, (client_payload, ROUTER_HOST, ROUTER_PORT))


# Commands
# REGISTER
# SEND_MSG <RECV> <MSG>
# CREATE_GROUP <NAME>
# JOIN_GROUP <NAME>
# LEAVE_GROUP <NAME>


def client_handler(connection, address):

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

    # TODO: do something with the payload
    print(payload["sender"], ":", payload["message"])

    connection.close()


def accept_connections(ServerSocket):
    client, address = ServerSocket.accept()
    # logger.info("Connected to: " + address[0] + ":" + str(address[1]))
    global_queue.dispatch_sync(client_handler, args=(client, address))
    # start_new_thread(client_handler, (client, address))


def router_listener():
    # Create a socket and bind to a port. SO_REUSEADDR=1 for reusing address
    ServerSocket = socket.socket()
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        ServerSocket.bind((HOST, PORT))
    except socket.error as e:
        logger.error(str(e))

    while True:
        print("Server is listening on the port {}".format(PORT))
        ServerSocket.listen()
        try:
            accept_connections(ServerSocket)
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt")
            break


def main():
    # Create a socket and bind to a port. SO_REUSEADDR=1 for reusing address
    t1 = threading.Thread(target=router_listener)
    t2 = threading.Thread(target=message_sender)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
