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
        self.running = False

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.settimeout(1.0)
        self.server_socket = server
        self.running = True

        try:
            server.bind((self.host, self.port))
            server.listen()

            print(f"Peer {self.peer_id} listening on port {self.port}")

            while self.running:
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self.running:
                        raise
                    break

                thread = threading.Thread(
                    target=self.handle_connection,
                    args=(conn, addr)
                )
                thread.daemon = True
                thread.start()
        finally:
            self.running = False
            server.close()
            self.server_socket = None

    def handle_connection(self, conn, addr):
        # handshake, bitfield exchange, and starting the receive loop all
        # happen inside register_incoming_connection now
        self.connection_manager.register_incoming_connection(conn)

    def stop(self):
        self.running = False
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass
