import socket
import json
import time
from _thread import *
import argparse
from datetime import datetime
from pycentraldispatch import PyCentralDispatch
from CustomLog import *
import server_config

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default=None, help="Host IP address")
parser.add_argument("--port", type=int, default=9999, help="Port number")
parser.add_argument("--ID", type=int, required=True, help="Server ID")
parser.add_argument("--passive", action="store_true", help="Passive mode (receive requests but do not respond)")
#!parser.add_argument("--primary_passive", action="store_true", help="Primary passive replica (respond in passive mode)")
args = parser.parse_args()

#only the RM should touch this
PRIMARY_PASSIVE = False

HOST = "0.0.0.0" if args.host is None else args.host
PORT = args.port
ID = args.ID

state = 0.0 # state should always be a float

local_backup_list = []
for config in server_config.backup_list:
    if config[1] != PORT:
        local_backup_list.append(config)


BACKUP_S2_HOST = local_backup_list[0][0]
BACKUP_S2_PORT = local_backup_list[0][1]
BACKUP_S3_HOST = local_backup_list[1][0]
BACKUP_S3_PORT = local_backup_list[1][1]

# Variables for checkpointing
CHECKPOINT_FREQ = 1  # Set the checkpoint frequency (in seconds)
CHECKPOINT_COUNT = 0
FIRST_CHECKPOINT = 0

# Simon S's code for serialized dispatcher
# instantiate serialized dispatcher
global_queue = PyCentralDispatch.global_queue()

def client_handler(connection, address):
    global state, FIRST_CHECKPOINT, PRIMARY_PASSIVE

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
        
    
    if "hb_count" in payload.keys():  # LFD heartbeat
        logger.heartbeat("[{}]: {}".format(datetime.utcnow().isoformat(), payload["inp"]))
        lfd_payload = {
            #"server_ID": "a"+str(ID),
            "hb_count": payload["hb_count"],
            "inp": payload["inp"],
        }

        #designating type for memebership
        if args.passive:
            lfd_payload["server_ID"] = "p" + str(ID)
            #add passive to config file: 3rd item in list; match port
            for config in server_config.backup_list:
                if config[1] == PORT:
                    config[2] = lfd_payload["server_ID"]
        else:
            lfd_payload["server_ID"] = "a" + str(ID)
        
        try:
            connection.sendall(json.dumps(lfd_payload).encode("utf-8"))
        except socket.error as e:
            logger.error("[ERROR] Cannot send to LFD " + str(e))

    elif 'ckptID' in payload.keys():  # Checkpoint message
        # State before
        logger.state(
            "my_state_S{} = {} before processing checkpoint {}".format(
                ID, state, payload["ckptID"]
            )
        )
        # Receive checkpoint
        logger.receive_checkpoint(f"Server {ID}: Checkpoint message:{payload['inp']} ")
        # Change state
        state = payload["inp"]
        # State After
        logger.state(
            "my_state_S{} = {} after processing checkpoint {}".format(
                ID, state, payload["ckptID"]
            )
        )
        FIRST_CHECKPOINT = 1

    elif 'primary' in payload.keys():
        PRIMARY_PASSIVE = True
        logger.state(
            "[{}]: Server S{} has been elected as Primary".format(
                datetime.utcnow().isoformat(), ID
            )
        )

    else:
        client_ID = payload["client_ID"]
        message = payload["inp"]
        ReqNum = payload["ReqNum"]
        if args.passive and not PRIMARY_PASSIVE:
            # making first connection
            server_payload = {"server_ID": -2}
            try:
                connection.sendall(json.dumps(server_payload).encode("utf-8"))

            except socket.error as e:
                logger.error("[ERROR] Cannot send NULL message to client " + str(e))
            return
        # Acknowledge message received
        logger.receive(
            "[{}]: Received <C{}, S{}, {}, request>".format(
                datetime.utcnow().isoformat(), client_ID, ID, ReqNum
            )
        )
    
        # State before
        logger.state(
            "[{}]: my_state_S{} = {} before processing <C{}, S{}, {}, request>".format(
                datetime.utcnow().isoformat(), ID, state, client_ID, ID, ReqNum
            )
        )
        # Change state
        state = message
        # State After
        logger.state(
            "[{}]: my_state_S{} = {} after processing <C{}, S{}, {}, request>".format(
                datetime.utcnow().isoformat(), ID, state, client_ID, ID, ReqNum
            )
        )
        # Send reply back to client
        if args.passive and not PRIMARY_PASSIVE:
            logger.receive(
            "[{}]: Received <C{}, S{}, {}, request>".format(
                datetime.utcnow().isoformat(), client_ID, ID, ReqNum
            )
            )
            connection.close()
            return
        else:
            # making first connection
            server_payload = {"server_ID": ID, "inp": message.upper(), "ReqNum": ReqNum}
            try:
                connection.sendall(json.dumps(server_payload).encode("utf-8"))
                logger.send(
                "[{}]: Sent <C{}, S{}, {}, reply>".format(
                    datetime.utcnow().isoformat(), client_ID, ID, ReqNum
                )
            )
            except socket.error as e:
                logger.error("[ERROR] Cannot send to client " + str(e))

       
    
    connection.close()

def accept_connections(ServerSocket):
    client, address = ServerSocket.accept()
    # logger.info("Connected to: " + address[0] + ":" + str(address[1]))
    global_queue.dispatch_sync(client_handler, args=(client, address))
    # start_new_thread(client_handler, (client, address))

def send_checkpoint_message():
    global CHECKPOINT_COUNT, state

    # Increment checkpoint count
    CHECKPOINT_COUNT += 1

    # Prepare checkpoint message
    checkpoint_message = {
        "ckptID": CHECKPOINT_COUNT, 
        "inp": state, 
    }

    # Send checkpoint message to backup replica S2
    try:
        backup_s2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backup_s2_socket.connect((BACKUP_S2_HOST, BACKUP_S2_PORT))
        backup_s2_socket.sendall(json.dumps(checkpoint_message).encode("utf-8"))
        logger.info("Checkpoint {} message sent to backup replica S2: {}".format(CHECKPOINT_COUNT, state))
        backup_s2_socket.close()
    except socket.error as e:
        logger.error("Error while sending checkpoint message to S2: " + str(e))

    # Send checkpoint message to backup replica S3
    try:
        backup_s3_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backup_s3_socket.connect((BACKUP_S3_HOST, BACKUP_S3_PORT))
        backup_s3_socket.sendall(json.dumps(checkpoint_message).encode("utf-8"))
        logger.info("Checkpoint {} message sent to backup replica S3: {}".format(CHECKPOINT_COUNT, state))
        backup_s3_socket.close()
    except socket.error as e:
        logger.error("Error while sending checkpoint message to S3: " + str(e))

if __name__ == "__main__":
    start = time.time()

    # Create a socket and bind to a port. SO_REUSEADDR=1 for reusing address
    ServerSocket = socket.socket()
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        ServerSocket.bind((HOST, PORT))
    except socket.error as e:
        logger.error(str(e))

    print("Server started with state {}".format(state))
    
    # Accept connections forever
    while True:
        ServerSocket.listen()
        try:
            accept_connections(ServerSocket)
            if PRIMARY_PASSIVE and (time.time() - start >= CHECKPOINT_FREQ):
                send_checkpoint_message()
                start = time.time()
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt")
            break