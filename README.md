# PeerLink

## Clients

To open new clients, run following commands in separate terminals
```python
python Client/client.py --ID peer1 --port 8000
python Client/client.py --ID peer2 --port 8001
python Client/client.py --ID peer3 --port 8002
```

## Server

To start server and backups, run following commands in separate terminals
```python
python Server/server.py --port 8008
python Server/server.py --port 8009 --backup
python rm.py
```
