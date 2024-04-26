import socket
import json
import sys
import threading

sys.path.append("")
sys.path.append("../")
from CustomLog import *
from _thread import *


class ReturnValueThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None

    def run(self):
        if self._target is None:
            return  # could alternatively raise an exception, depends on the use case
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as exc:
            print(
                f"{type(exc).__name__}: {exc}", file=sys.stderr
            )  # properly handle the exception

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self.result


def send_msg(client_payload, host, port):

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        # print(f"Connected to server {host_list[ind][0]}:{host_list[ind][1]}")
    except socket.error as e:
        logger.error(f"Trying to connect to server {host}:{port}, Error: {str(e)}")

    try:
        # Send data
        sock.send(json.dumps(client_payload).encode("utf-8"))

        logger.send("Sent", client_payload)

        # # Receive data from the server
        # received = json.loads(sock.recv(1024).decode("utf-8"))

    except socket.error as e:
        logger.error("Client is down " + str(e))
        return False
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt")
        return False
    except Exception as e:
        logger.error("[ERROR] " + str(e))
        return False

    return True


class Client:
    def __init__(self, ID, host, port):
        self.ID = ID
        self.host = host
        self.port = port
        self.queue = []


class Server:
    def __init__(self):
        self.client_addr = {}
        self.group_addr = {}

    def register_client(self, payload, address):
        client_name = payload["message"]
        if client_name not in self.client_addr.keys():
            self.client_addr[client_name] = Client(
                client_name, address[0], payload["port"]
            )
        else:
            self.client_addr[client_name].host = address[0]
            self.client_addr[client_name].port = payload["port"]
        logger.info(f"Registered client {client_name} at {address[0]}:{address[1]}")
        # Check if queue is empty
        if len(self.client_addr[client_name].queue) > 0:
            # Send messages in queue
            i = 0
            while i < len(self.client_addr[client_name].queue):
                send_payload = self.client_addr[client_name].queue[i]
                print("Sending ", send_payload["message"])
                thread = ReturnValueThread(
                    target=send_msg,
                    args=(
                        send_payload,
                        self.client_addr[client_name].host,
                        self.client_addr[client_name].port,
                    ),
                )
                thread.start()
                success = thread.join()
                if success:
                    self.client_addr[client_name].queue.remove(send_payload)
                    print("Sent ", send_payload["message"])
                else:
                    i += 1
        return True

    def send_msg(self, payload):
        sender = payload["sender"]
        message = payload["message"]

        # Check if recipient exists
        if payload["recipient"] in self.client_addr:
            client_name = payload["recipient"]
            recipient = self.client_addr[client_name]
            send_payload = {"sender": sender, "message": message}
            thread = ReturnValueThread(
                target=send_msg, args=(send_payload, recipient.host, recipient.port)
            )
            thread.start()
            success = thread.join()
            # print("success:", success)
            # add to queue when false
            if not success:
                recipient.queue.append(send_payload)
            return success

        # Check if recipient is a group
        elif payload["recipient"] in self.group_addr:
            group_name = payload["recipient"]

            # Send message to group members
            successes = []
            for client in self.group_addr[group_name]:
                # Don't send message to yourself
                if client.ID == sender:
                    continue

                send_payload = {
                    "sender": f"{sender} ({group_name})",
                    "message": message,
                }
                thread = ReturnValueThread(
                    target=send_msg, args=(send_payload, client.host, client.port)
                )
                thread.start()
                successes.append(thread.join())
            return successes[0]  # TODO: how to deal with message status in groups?
        else:
            logger.error(f"Recipient {payload['recipient']} not found")
            return False

    def create_group(self, payload):
        sender = payload["sender"]
        group_name = payload["message"]

        # Check if group exists
        if group_name in self.group_addr:
            logger.error(f"Group {group_name} already exists")
            return False
        else:
            self.group_addr[group_name] = [self.client_addr[sender]]
            logger.info(f"Created group {group_name}")
        return True

    def join_group(self, payload):
        sender = payload["sender"]
        group_name = payload["message"]

        # Check if group exists
        if group_name not in self.group_addr:
            logger.error(f"Group {group_name} not found")
            return False
        else:
            self.group_addr[group_name].append(self.client_addr[sender])
            logger.info(f"Client {sender} joined group {group_name}")
        return True

    def leave_group(self, payload):
        sender = payload["sender"]
        group_name = payload["message"]

        # Check if group exists
        if group_name not in self.group_addr:
            logger.error(f"Group {group_name} not found")
            return False
        else:
            self.group_addr[group_name].remove(self.client_addr[sender])
            logger.info(f"Client {sender} left group {group_name}")
        return True
