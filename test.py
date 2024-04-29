import unittest
import subprocess
from subprocess import Popen
from subprocess import PIPE
import time


class TestClient(unittest.TestCase):

    def kill_process(self, process):
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
        process.kill()
        process.wait()

    def new_client(self, ID, port):
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

    def setUp(self):
        # Launch the server process in a new terminal window with stdout redirected to a pipe
        self.sp = self.new_server("8008", backup=False)
        # print("Server done")
        # Wait for the server to start up
        time.sleep(0.5)
        self.client1 = self.new_client("peer1", "8000")
        self.client2 = self.new_client("peer2", "8001")

    def tearDown(self):
        # Terminate running processes
        self.kill_process(self.sp)
        self.kill_process(self.client1)
        self.kill_process(self.client2)

    def test_register(self):

        # Send a command to the client process
        self.write_command(self.client1, "REGISTER\n")
        self.check_output(self.sp, "Client peer1 registered successfully")
        self.write_command(self.client2, "REGISTER\n")
        self.check_output(self.sp, "Client peer2 registered successfully")


if __name__ == "__main__":
    unittest.main()