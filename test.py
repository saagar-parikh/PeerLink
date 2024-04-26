import unittest
import threading
import socket
import json
import time
from _thread import *

HOST = "localhost"
PORT = 12346


class Client:
    def __init__(self, client_id):
        self.client_id = client_id

    def send_message(self, recipient, message):
        client_payload = {
            "command": "SEND_MSG",
            "sender": self.client_id,
            "recipient": recipient,
            "message": message,
        }
        return self.send_test_message(client_payload)

    def register(self):
        client_payload = {"command": "REGISTER", "sender": self.client_id}
        return self.send_test_message(client_payload)

    def create_group(self, group_name):
        client_payload = {
            "command": "CREATE_GROUP",
            "sender": self.client_id,
            "message": group_name,
        }
        return self.send_test_message(client_payload)

    def join_group(self, group_name):
        client_payload = {
            "command": "JOIN_GROUP",
            "sender": self.client_id,
            "message": group_name,
        }
        return self.send_test_message(client_payload)

    def leave_group(self, group_name):
        client_payload = {
            "command": "LEAVE_GROUP",
            "sender": self.client_id,
            "message": group_name,
        }
        return self.send_test_message(client_payload)

    def send_test_message(self, client_payload):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            sock.send(json.dumps(client_payload).encode("utf-8"))
            response_data = sock.recv(2048).decode("utf-8")
            response = json.loads(response_data)
        return response


class TestClientServer(unittest.TestCase):
    def setUp(self):
        self.ServerSocket = socket.socket()
        self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ServerSocket.bind((HOST, PORT))
        self.ServerSocket.listen(1)

        # Start the test server in a separate thread
        start_new_thread(self.start_test_server, ())

        # Wait for the server to start
        time.sleep(0.1)

    def tearDown(self):
        # Stop the test server
        self.ServerSocket.close()
        print("test complete")
        # print("done")

    def start_test_server(self):

        while True:
            try:
                print("Waiting to accept")
                client, address = self.ServerSocket.accept()
            except:
                print("Breaking")
                break

            print("Handling client request")
            start_new_thread(self.handle_test_client, (client, address))
            print("Handled client request")

    def handle_test_client(self, client, address):
        data = client.recv(2048).decode("utf-8")
        client_payload = json.loads(data)

        if client_payload["command"] == "REGISTER":
            response = {"status": "registered", "client_id": client_payload["sender"]}
        elif client_payload["command"].startswith("SEND_MSG"):
            response = {"status": "message_sent"}
        elif client_payload["command"].startswith("CREATE_GROUP"):
            response = {
                "status": "group_created",
                "group_name": client_payload["message"],
            }
        elif client_payload["command"].startswith("JOIN_GROUP"):
            response = {
                "status": "joined_group",
                "group_name": client_payload["message"],
            }
        elif client_payload["command"].startswith("LEAVE_GROUP"):
            response = {"status": "left_group", "group_name": client_payload["message"]}
        else:
            response = {"status": "unknown_command"}

        client.send(json.dumps(response).encode("utf-8"))
        client.close()

    def test_register_command(self):
        client = Client("test_client")
        response = client.register()
        self.assertEqual(response["status"], "registered")
        self.assertEqual(response["client_id"], "test_client")

    def test_send_message_command(self):
        client1 = Client("sender_client")
        client2 = Client("recipient_client")

        # Register both clients
        client1.register()
        client2.register()

        response = client1.send_message("recipient_client", "Hello")
        self.assertEqual(response["status"], "message_sent")

    def test_create_group_command(self):
        client = Client("test_client")
        response = client.create_group("test_group")
        self.assertEqual(response["status"], "group_created")
        self.assertEqual(response["group_name"], "test_group")

    def test_join_group_command(self):
        client1 = Client("test_client")
        client2 = Client("another_client")

        # Create a group
        client1.create_group("test_group")

        response = client2.join_group("test_group")
        self.assertEqual(response["status"], "joined_group")
        self.assertEqual(response["group_name"], "test_group")

    def test_leave_group_command(self):
        client = Client("test_client")
        client.create_group("test_group")

        response = client.leave_group("test_group")
        self.assertEqual(response["status"], "left_group")
        self.assertEqual(response["group_name"], "test_group")


if __name__ == "__main__":
    unittest.main()
