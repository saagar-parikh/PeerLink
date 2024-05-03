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

        logger.send(f"Sent {client_payload}", client_payload)

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
    def __init__(self, ID, host, port, queue=[]):
        self.ID = ID
        self.host = host
        self.port = port
        self.queue = queue


class Server:
    def __init__(self):
        self.client_addr = {}
        self.group_addr = {}

    def to_dict(self):
        server_dict = {
            "client_addr": {
                client_id: client.__dict__
                for client_id, client in self.client_addr.items()
            },
            "group_addr": self.group_addr,
        }
        return server_dict

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    @classmethod
    def from_json(cls, server_dict):
        # server_dict = json.loads(json_data)
        server = cls()
        server.client_addr = {
            client_id: Client(**client_data)
            for client_id, client_data in server_dict["client_addr"].items()
        }
        server.group_addr = server_dict["group_addr"]
        return server

    def register_client(self, payload, address):
        client_name = payload["message"]
        if client_name not in self.client_addr.keys():
            self.client_addr[client_name] = Client(
                client_name, address[0], payload["port"]
            )
        else:
            # Reconnection
            self.client_addr[client_name].host = address[0]
            self.client_addr[client_name].port = payload["port"]
        logger.info(f"Registered client {client_name} at {address[0]}:{address[1]}")
        # Check if queue is empty
        if len(self.client_addr[client_name].queue) > 0:
            # Send messages in queue
            i = 0
            while i < len(self.client_addr[client_name].queue):
                send_payload = self.client_addr[client_name].queue[i]
                logger.send("Sending ", send_payload["message"])
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
                    logger.send("Sent ", send_payload["message"])
                else:
                    i += 1
        success = {client_name: True}
        logger.send(f"Registered {client_name}. Success: {success}")
        return success

    def send_msg_command(self, payload):
        logger.info("Start send_msg_command")
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
            success = {}
            success[recipient.ID] = thread.join()
            # print("success:", success)
            # add to queue when false
            if not success[recipient.ID]:
                recipient.queue.append(send_payload)
            logger.info("Sent to", recipient.ID, recipient.port, success[recipient.ID])
            return success

        # Check if recipient is a group
        elif payload["recipient"] in self.group_addr:
            group_name = payload["recipient"]

            # Send message to group members
            successes = {}
            for client_name in self.group_addr[group_name]:
                client = self.client_addr[client_name]
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
                successes[client.ID] = thread.join()

            return successes
            # return [
            #     self.group_addr[i].ID
            #     for i in range(len(self.group_addr))
            #     if successes[i]
            # ]  # TODO: how to deal with message status in groups?
        else:
            logger.error(f"Recipient {payload['recipient']} not found")
            return {payload["recipient"]: False}

    def create_group(self, payload):
        sender = payload["sender"]
        group_name = payload["message"]

        # Check if group exists
        if group_name in self.group_addr:
            logger.error(f"Group {group_name} already exists")
            return {group_name: False}
        else:
            self.group_addr[group_name] = [sender]
            logger.info(f"Created group {group_name}")
        return {group_name: True}

    def join_group(self, payload):
        sender = payload["sender"]
        group_name = payload["message"]

        # Check if group exists
        if group_name not in self.group_addr:
            logger.error(f"Group {group_name} not found")
            return {group_name: False}
        else:
            self.group_addr[group_name].append(sender)
            logger.info(f"Client {sender} joined group {group_name}")
        return {group_name: True}

    def leave_group(self, payload):
        sender = payload["sender"]
        group_name = payload["message"]

        # Check if group exists
        if group_name not in self.group_addr:
            logger.error(f"Group {group_name} not found")
            return {group_name: False}
        else:
            self.group_addr[group_name].remove(sender)
            logger.info(f"Client {sender} left group {group_name}")
        return {group_name: True}
