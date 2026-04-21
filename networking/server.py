import socket
import threading

from networking.connection_manager import ConnectionManager


class TCPServer:

    def __init__(
            self,
            peer_id: int,
            host: str,
            port: int,
            connection_manager: ConnectionManager
    ):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.connection_manager = connection_manager
        self.server_socket = None

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket = server

        try:
            server.bind((self.host, self.port))
            server.listen()

            print(f"Peer {self.peer_id} listening on port {self.port}")

            while True:
                conn, addr = server.accept()

                thread = threading.Thread(
                    target=self.handle_connection,
                    args=(conn, addr)
                )
                thread.daemon = True
                thread.start()
        finally:
            server.close()
            self.server_socket = None

    def handle_connection(self, conn, addr):
        # handshake, bitfield exchange, and starting the receive loop all
        # happen inside register_incoming_connection now
        self.connection_manager.register_incoming_connection(conn)
