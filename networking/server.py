import socket
import threading

from networking.connection_manager import ConnectionManager
from protocol.encoder import encode_bitfield, encode_interested, encode_not_interested
from protocol.decoder import recv_message, decode_bitfield_payload
from protocol.message_types import MessageType


class TCPServer:

    def __init__(
            self,
            peer_id: int,
            host: str,
            port: int,
            connection_manager: ConnectionManager,
            piece_manager,
            common_cfg
    ):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.connection_manager = connection_manager
        self.piece_manager = piece_manager
        self.common_cfg = common_cfg

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

    def handle_connection(self, conn, addr):
        # Handshake is done inside register_incoming_connection
        remote_id = self.connection_manager.register_incoming_connection(conn)

        # Bitfield exchange
        conn.sendall(encode_bitfield(self.piece_manager.bitfield))
        print(f"Peer {self.peer_id} sent bitfield ({self.piece_manager.piece_count()} pieces)")

        msg = recv_message(conn)
        if msg.msg_type == MessageType.BITFIELD:
            remote_bitfield = decode_bitfield_payload(msg.payload, self.common_cfg.num_pieces)
            print(f"Peer {self.peer_id} received bitfield from {remote_id} ({remote_bitfield.piece_count()} pieces)")

            # Interested / Not Interested
            has_something_we_need = False
            for i in range(self.common_cfg.num_pieces):
                if remote_bitfield.has_piece(i) and not self.piece_manager.bitfield.has_piece(i):
                    has_something_we_need = True
                    break

            if has_something_we_need:
                conn.sendall(encode_interested())
                print(f"Peer {self.peer_id} sending INTERESTED to {remote_id}")
            else:
                conn.sendall(encode_not_interested())
                print(f"Peer {self.peer_id} sending NOT_INTERESTED to {remote_id}")
