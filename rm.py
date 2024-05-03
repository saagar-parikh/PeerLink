import socket
import json
import sys
import time
from _thread import *
import argparse
from datetime import datetime
from pycentraldispatch import PyCentralDispatch
from CustomLog import *

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost", help="Host IP address")
parser.add_argument("--port", type=int, default=9000, help="Port number")

args = parser.parse_args()


HOST = args.host
PORT = args.port


# instantiate serialized dispatcher
global_queue = PyCentralDispatch.global_queue()


HOST_LIST = [("localhost", 8008), ("localhost", 8009)]  # , ("localhost", 8010)]
CLIENT_LIST = [("localhost", 8000), ("localhost", 8001), ("localhost", 8002)]
HEARTBEAT_INTERVAL = 2
primary_idx = 0


def send_heartbeat_msg(host, port):
    """
    Send a heartbeat message to the specified host and port

    host: The IP address of the host
    port: The port number
    """

    hb_payload = json.dumps({"command": "HEARTBEAT"})
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        # logger.info(f"Connected to server {host_list[ind][0]}:{host_list[ind][1]}")
    except socket.error as e:
        logger.error(f"Trying to connect to server {host}:{port}, Error: {str(e)}")

    try:
        # Send data
        sock.send(hb_payload.encode("utf-8"))

        logger.send(f"Sent     heartbeat to   {host}:{port}")

        # Receive data from the server
        received = json.loads(sock.recv(1024).decode("utf-8"))

        logger.receive(f"Received heartbeat from {host}:{port}. Success: {received}")

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


def send_update_msg(host, port, primary_idx):
    """
    Send an update message to the specified host and port to inform about the change in primary server

    host: The IP address of the host
    port: The port number
    primary_idx: Index of the new primary server in the HOST_LIST
    """

    logger.info(f"Send update msg started for {host}:{port}")
    update_payload = {"command": "UPDATE_PRIMARY", "primary_idx": primary_idx}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        logger.info(f"Connected to server {host}:{port}")
    except socket.error as e:
        logger.error(f"Trying to connect to server {host}:{port}, Error: {str(e)}")

    try:
        # Send data
        sock.send(json.dumps(update_payload).encode("utf-8"))

        logger.send(f"Sent     update to   {host}:{port}")

        # # Receive data from the server
        # received = json.loads(sock.recv(1024).decode("utf-8"))
        # logger.receive(
        #     f"Received update from {host}:{port}. Success: {received['success']}"
        # )

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


def change_primary_server():
    """
    Change the primary server to the next server in the HOST_LIST.
    This function is called when the primary server is down.
    """

    global primary_idx
    primary_idx = (primary_idx + 1) % len(HOST_LIST)
    logger.warn(f"Primary server changed to {HOST_LIST[primary_idx]}")
    print("Primary server changed")
    sys.stdout.flush()

    # Send message to backup that it is primary
    send_update_msg(HOST_LIST[primary_idx][0], HOST_LIST[primary_idx][1], primary_idx)

    # Send message to all clients to update primary server
    for host, port in CLIENT_LIST:
        send_update_msg(host, port, primary_idx)


def send_heartbeat_msg_to_all(primary_idx=0):
    """
    Send heartbeat messages to all servers in the HOST_LIST.
    This function is called periodically to check the status of all servers.
    If the primary server is down, it calls the change_primary_server function.

    primary_idx: Index of the current primary server in the HOST_LIST.
    """

    global HOST_LIST
    for i, (host, port) in enumerate(HOST_LIST):
        success = send_heartbeat_msg(host, port)
        if not success:
            if i == primary_idx:
                logger.warn(f"Primary server {host}:{port} is down")
                # update primary_idx and send message to all clients
                start_new_thread(change_primary_server, ())
            # else:
            #     pass  # TODO: Note that particular backup is down


def main():
    global primary_idx
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        send_heartbeat_msg_to_all(primary_idx)


if __name__ == "__main__":
    main()
