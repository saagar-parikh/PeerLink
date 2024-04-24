import socket
import json
from CustomLog import *
from _thread import *


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


class Client:
    def __init__(self, ID, host, port):
        self.ID = ID
        self.host = host
        self.port = port


class Server:
    def __init__(self):
        self.client_addr = {}
        self.group_addr = {}

    def register_client(self, payload, address):
        self.client_addr[payload["message"]] = Client(
            payload["message"], address[0], payload["port"]
        )
        logger.info(
            f"Registered client {payload['message']} at {address[0]}:{address[1]}"
        )

    def send_msg(self, payload):
        # Check if recipient exists
        if payload["recipient"] not in self.client_addr:
            logger.error(f"Recipient {payload['recipient']} not found")
            return
        else:
            recipient = self.client_addr[payload["recipient"]]
            message = payload["message"]
            send_payload = {"sender": payload["sender"], "message": message}
            start_new_thread(send_msg, (send_payload, recipient.host, recipient.port))

    def create_group(self, payload):
        pass

    def join_group(self, payload):
        pass

    def leave_group(self, payload):
        pass
