import socket


def connect_to_peer(
        host: str, 
        port: int
    ) -> socket.socket:

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    return sock
