import os
import unittest
import subprocess
from subprocess import Popen
from subprocess import PIPE
import time


class BaseTestClient(unittest.TestCase):

    def kill_process(self, process):
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
        process.kill()
        process.wait()

    def new_client(self, ID, port, show_logs=False):
        if show_logs:
            client_args = [
                "/usr/bin/python3",
                "Client/client.py",
                "--ID",
                ID,
                "--port",
                port,
                "--show_logs",
                "true",
            ]

        else:
            client_args = [
                "/usr/bin/python3",
                "Client/client.py",
                "--ID",
                ID,
                "--port",
                port,
            ]
        return Popen(client_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def new_server(self, port, backup=False):
        if backup:
            server_args = [
                "/usr/bin/python3",
                "Server/server.py",
                "--port",
                port,
                "--backup",
            ]
        else:
            server_args = [
                "/usr/bin/python3",
                "Server/server.py",
                "--port",
                port,
            ]
        return Popen(server_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def write_command(self, process, command):
        process.stdin.write(command.encode())
        process.stdin.flush()

    def check_output(self, process, expected):
        line = process.stdout.readline()
        self.assertEqual(line.decode().strip(), expected)

    def get_output(self, process):
        line = process.stdout.readline()
        return line.decode().strip()

    def check_output(self, process, expected):
        try:
            line = process.stdout.readline()
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            return
        self.assertEqual(line.decode().strip(), expected)

    def setUp(self):
        os.system("fuser -k 8000/tcp")
        os.system("fuser -k 8001/tcp")
        os.system("fuser -k 8002/tcp")
        os.system("fuser -k 8050/tcp")
        os.system("fuser -k 8008/tcp")
        # Launch the server process in a new terminal window with stdout redirected to a pipe
        self.sp = self.new_server("8008", backup=False)
        # print("Server done")
        # Wait for the server to start up
        time.sleep(0.5)
        self.client1 = self.new_client("peer1", "8000")
        self.client2 = self.new_client("peer2", "8001")
        self.client3 = self.new_client("peer3", "8002")

        # For checking logs
        self.client4 = self.new_client("peer4", "8050", True)
        # self.client5 = self.new_client("peer5", "8051", True)
        # self.client6 = self.new_client("peer6", "8052", True)

    def tearDown(self):
        # Terminate running processes
        self.kill_process(self.sp)
        self.kill_process(self.client1)
        self.kill_process(self.client2)
        self.kill_process(self.client3)
        self.kill_process(self.client4)
        # self.kill_process(self.client5)
        # self.kill_process(self.client6)
        time.sleep(1)
        # print("tearDown done")


class TestRegister(BaseTestClient):

    def test_register(self):
        with self.subTest("Check peer1", i=0):
            self.write_command(self.client1, "REGISTER\n")
            self.check_output(self.sp, "Client peer1 registered successfully")
        with self.subTest("Check peer2", i=1):
            self.write_command(self.client2, "REGISTER\n")
            self.check_output(self.sp, "Client peer2 registered successfully")


class TestSendMsg(BaseTestClient):

    def test_send_msg(self):
        # Register all clients
        self.write_command(self.client1, "REGISTER\n")
        self.check_output(self.sp, "Client peer1 registered successfully")
        self.write_command(self.client2, "REGISTER\n")
        self.check_output(self.sp, "Client peer2 registered successfully")
        self.write_command(self.client3, "REGISTER\n")
        self.check_output(self.sp, "Client peer3 registered successfully")

        # Test peer to peer communication
        self.write_command(self.client1, "SEND_MSG peer2 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer1 : Hello")

        # Multiple clients send to same client
        self.write_command(self.client1, "SEND_MSG peer3 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client3, "peer1 : Hello")
        self.write_command(self.client2, "SEND_MSG peer3 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client3, "peer2 : Hello")

        # Single client sends messages to multiple clients. Test if message received
        self.write_command(self.client1, "SEND_MSG peer2 Hello again\n")
        self.write_command(self.client1, "SEND_MSG peer3 Hello again\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer1 : Hello again")
        self.check_output(self.client3, "peer1 : Hello again")


class TestGroupMsg(BaseTestClient):

    def test_group_msg(self):
        # Register all clients
        self.write_command(self.client1, "REGISTER\n")
        self.check_output(self.sp, "Client peer1 registered successfully")
        self.write_command(self.client2, "REGISTER\n")
        self.check_output(self.sp, "Client peer2 registered successfully")
        self.write_command(self.client3, "REGISTER\n")
        self.check_output(self.sp, "Client peer3 registered successfully")

        # Create group
        self.write_command(self.client1, "CREATE_GROUP group1\n")
        self.check_output(self.sp, "Group group1 created successfully")

        # Join group
        self.write_command(self.client2, "JOIN_GROUP group1\n")
        self.write_command(self.client3, "JOIN_GROUP group1\n")

        # 1. send message to group
        self.write_command(self.client1, "SEND_MSG group1 Hello group\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer1 (group1) : Hello group")
        self.check_output(self.client3, "peer1 (group1) : Hello group")
        # message not received by self

        # 2. Leave group and check
        self.write_command(self.client3, "LEAVE_GROUP group1\n")
        time.sleep(0.5)

        # Send message to group
        self.write_command(self.client1, "SEND_MSG group1 Hello group again\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer1 (group1) : Hello group again")
        # message not received by client3

        # 3. Rejoin group
        self.write_command(self.client3, "JOIN_GROUP group1\n")
        self.write_command(self.client2, "SEND_MSG group1 Hello group from peer2\n")
        time.sleep(0.5)
        self.check_output(self.client1, "peer2 (group1) : Hello group from peer2")
        self.check_output(self.client3, "peer2 (group1) : Hello group from peer2")

        # Create new groups
        self.write_command(self.client2, "CREATE_GROUP group2\n")
        time.sleep(0.5)
        self.check_output(self.sp, "Group group2 created successfully")

        self.write_command(self.client2, "CREATE_GROUP group3\n")
        time.sleep(0.5)
        self.check_output(self.sp, "Group group3 created successfully")

        # Join new group
        self.write_command(self.client3, "JOIN_GROUP group2\n")
        self.write_command(self.client1, "JOIN_GROUP group3\n")

        # At this stage
        # group1 has peer1, peer2, peer3
        # group2 has peer2, peer3
        # group3 has peer1, peer2
        # OR
        # peer1 is in group1, group3
        # peer2 is in group1, group2, group3
        # peer3 is in group1, group2

        # group1 message
        self.write_command(self.client3, "SEND_MSG group1 Hello group1\n")
        time.sleep(0.5)
        self.check_output(self.client1, "peer3 (group1) : Hello group1")
        self.check_output(self.client2, "peer3 (group1) : Hello group1")

        # group2 message
        self.write_command(self.client2, "SEND_MSG group2 Hello group2\n")
        time.sleep(0.5)
        self.check_output(self.client3, "peer2 (group2) : Hello group2")

        # group3 message
        self.write_command(self.client1, "SEND_MSG group3 Hello group3\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer1 (group3) : Hello group3")


class TestMsgStates(BaseTestClient):
    def test_msg_states(self):
        # Register all clients
        self.write_command(self.client4, "REGISTER\n")
        self.check_output(self.sp, "Client peer4 registered successfully")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer4")

        self.write_command(self.client1, "REGISTER\n")
        self.check_output(self.sp, "Client peer1 registered successfully")
        self.write_command(self.client2, "REGISTER\n")
        self.check_output(self.sp, "Client peer2 registered successfully")

        # Send message and check status
        self.write_command(self.client4, "SEND_MSG peer2 Hello\n")
        time.sleep(0.1)
        self.check_output(self.client4, "Sent")
        time.sleep(0.5)
        self.check_output(self.client2, "peer4 : Hello")
        self.check_output(self.client4, "Delivered to peer2")

        # Send group message and check status
        self.write_command(self.client1, "CREATE_GROUP group1\n")
        time.sleep(0.5)
        self.check_output(self.sp, "Group group1 created successfully")
        self.write_command(self.client2, "JOIN_GROUP group1\n")
        self.write_command(self.client4, "JOIN_GROUP group1\n")
        time.sleep(0.5)
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to group1")

        self.write_command(self.client4, "SEND_MSG group1 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client1, "peer4 (group1) : Hello")
        self.check_output(self.client2, "peer4 (group1) : Hello")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer1")
        self.check_output(self.client4, "Delivered to peer2")


class TestDisconnection(BaseTestClient):
    def test_disconnection(self):
        # Register all clients
        self.write_command(self.client1, "REGISTER\n")
        self.check_output(self.sp, "Client peer1 registered successfully")
        self.write_command(self.client2, "REGISTER\n")
        self.check_output(self.sp, "Client peer2 registered successfully")
        self.write_command(self.client3, "REGISTER\n")
        self.check_output(self.sp, "Client peer3 registered successfully")
        self.write_command(self.client4, "REGISTER\n")
        self.check_output(self.sp, "Client peer4 registered successfully")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer4")

        # Send message and check status
        self.write_command(self.client4, "SEND_MSG peer1 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client1, "peer4 : Hello")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer1")

        # Disconnect client1
        self.kill_process(self.client1)
        time.sleep(0.5)
        self.write_command(self.client4, "SEND_MSG peer1 Hello again\n")
        time.sleep(0.5)
        self.check_output(self.client4, "Sent")
        # no message is delivered to peer1

        # Disconnect from group
        self.write_command(self.client2, "CREATE_GROUP group1\n")
        time.sleep(0.5)
        self.check_output(self.sp, "Group group1 created successfully")
        self.write_command(self.client3, "JOIN_GROUP group1\n")
        self.write_command(self.client4, "JOIN_GROUP group1\n")
        time.sleep(0.5)
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to group1")

        self.kill_process(self.client3)
        self.write_command(self.client4, "SEND_MSG group1 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer4 (group1) : Hello")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer2")
        # No message is delivered to peer3


class TestReconnection(BaseTestClient):
    def test_reconnection(self):
        # Register all clients
        self.write_command(self.client1, "REGISTER\n")
        self.check_output(self.sp, "Client peer1 registered successfully")
        self.write_command(self.client2, "REGISTER\n")
        self.check_output(self.sp, "Client peer2 registered successfully")
        self.write_command(self.client3, "REGISTER\n")
        self.check_output(self.sp, "Client peer3 registered successfully")
        self.write_command(self.client4, "REGISTER\n")
        self.check_output(self.sp, "Client peer4 registered successfully")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer4")

        # Send message and check status
        self.write_command(self.client4, "SEND_MSG peer1 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client1, "peer4 : Hello")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer1")

        # Disconnect client1
        self.kill_process(self.client1)
        time.sleep(0.5)
        self.write_command(self.client4, "SEND_MSG peer1 Hello again\n")
        time.sleep(0.5)
        self.check_output(self.client4, "Sent")
        # no message is delivered to peer1

        # Reconnect client1 and check that waiting messages are delivered
        self.client1 = self.new_client("peer1", "8000")
        self.write_command(self.client1, "REGISTER\n")
        self.check_output(self.sp, "Client peer1 registered successfully")
        self.check_output(self.client1, "peer4 : Hello again")
        self.write_command(self.client4, "SEND_MSG peer1 Welcome back\n")
        time.sleep(0.5)
        self.check_output(self.client1, "peer4 : Welcome back")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer1")

        # Disconnect from group
        self.write_command(self.client2, "CREATE_GROUP group1\n")
        time.sleep(0.5)
        self.check_output(self.sp, "Group group1 created successfully")
        self.write_command(self.client3, "JOIN_GROUP group1\n")
        self.write_command(self.client4, "JOIN_GROUP group1\n")
        time.sleep(0.5)
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to group1")

        self.kill_process(self.client3)
        self.write_command(self.client4, "SEND_MSG group1 Hello\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer4 (group1) : Hello")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer2")
        # No message is delivered to peer3

        # Reconnect peer3
        self.client3 = self.new_client("peer3", "8002")
        self.write_command(self.client3, "REGISTER\n")
        self.check_output(self.sp, "Client peer3 registered successfully")
        # Should not receive waiting messages because it was a group message

        self.write_command(self.client4, "SEND_MSG group1 Hello again\n")
        time.sleep(0.5)
        self.check_output(self.client2, "peer4 (group1) : Hello again")
        self.check_output(self.client3, "peer4 (group1) : Hello again")
        self.check_output(self.client4, "Sent")
        self.check_output(self.client4, "Delivered to peer2")
        self.check_output(self.client4, "Delivered to peer3")


# class TestReplication(BaseTestClient):
#     def setUp(self):
#         super().setUp()
#         self.backup = self.new_server("8009", backup=True)
#         self.rm = Popen(
#             ["/usr/bin/python3", "RM/rm.py"], stdin=PIPE, stdout=PIPE, stderr=PIPE
#         )
#         time.sleep(0.5)

#     def tearDown(self):
#         super().tearDown()
#         self.kill_process(self.backup)
#         self.kill_process(self.rm)

#     def test_replication(self):
#         # Register all clients
#         self.write_command(self.client1, "REGISTER\n")
#         self.check_output(self.sp, "Client peer1 registered successfully")
#         self.write_command(self.client2, "REGISTER\n")
#         self.check_output(self.sp, "Client peer2 registered successfully")
#         self.write_command(self.client3, "REGISTER\n")
#         self.check_output(self.sp, "Client peer3 registered successfully")

#         # Send message and check status
#         self.write_command(self.client1, "SEND_MSG peer2 Hello\n")
#         time.sleep(0.5)
#         self.check_output(self.client2, "peer1 : Hello")

#         # Check backup receiving checkpoint
#         time.sleep(4)
#         # Kill primary server
#         self.kill_process(self.sp)
#         time.sleep(2)
#         print("server killed")
#         # Send message and check status
#         self.write_command(self.client2, "SEND_MSG peer1 Hello\n")
#         time.sleep(0.5)
#         self.check_output(self.client1, "peer2 : Hello")


if __name__ == "__main__":
    os.system("fuser -k 8000/tcp")
    os.system("fuser -k 8001/tcp")
    os.system("fuser -k 8002/tcp")
    os.system("fuser -k 8050/tcp")
    os.system("fuser -k 8008/tcp")
    os.system("fuser -k 8009/tcp")
    os.system("fuser -k 9000/tcp")
    register = unittest.TestLoader().loadTestsFromTestCase(TestRegister)
    send_msg = unittest.TestLoader().loadTestsFromTestCase(TestSendMsg)
    group_msg = unittest.TestLoader().loadTestsFromTestCase(TestGroupMsg)
    msg_states = unittest.TestLoader().loadTestsFromTestCase(TestMsgStates)
    disconnection = unittest.TestLoader().loadTestsFromTestCase(TestDisconnection)
    reconnection = unittest.TestLoader().loadTestsFromTestCase(TestReconnection)
    # replication = unittest.TestLoader().loadTestsFromTestCase(TestReplication)

    runner = unittest.TextTestRunner()
    register_result = runner.run(register)
    send_msg_result = runner.run(send_msg)
    group_msg_result = runner.run(group_msg)
    msg_states_result = runner.run(msg_states)
    disconnection_result = runner.run(disconnection)
    reconnection_result = runner.run(reconnection)
    # replication_result = runner.run(replication)

    passed = 0
    count = 0
    if register_result.wasSuccessful():
        passed += 10
        count += 1
    if send_msg_result.wasSuccessful():
        passed += 10
        count += 1
    if group_msg_result.wasSuccessful():
        passed += 15
        count += 1
    if msg_states_result.wasSuccessful():
        passed += 15
        count += 1
    if disconnection_result.wasSuccessful():
        passed += 10
        count += 1
    if reconnection_result.wasSuccessful():
        passed += 20
        count += 1
    # if replication_result.wasSuccessful():
    #     passed += 20
    #     count += 1

    print(f"Passed {count}/7 tests.\nTotal score: {passed}/100")
    # unittest.main()
