from networking.client import connect_to_peer
from protocol import handshake
from protocol.encoder import encode_bitfield, encode_interested, encode_not_interested
from protocol.decoder import recv_message, decode_bitfield_payload
from protocol.message_types import MessageType


class ConnectionManager:

    def __init__(self, peer_id, peer_info_list, piece_manager):

        self.peer_id = peer_id
        self.peer_info_list = peer_info_list
        self.piece_manager = piece_manager

        # peer_id -> socket
        self.connections = {}

    def start_outgoing_connections(self):

        for peer in self.peer_info_list:

            # only connect to peers with smaller ID to have 1 connection between each pair

            if peer.peer_id < self.peer_id:

                sock = connect_to_peer(peer.hostname, peer.port)

                if sock:
                    # Send our ID, then read theirs to confirm who answered
                    handshake.send(sock, self.peer_id)
                    remote_id = handshake.receive(sock)

                    if remote_id != peer.peer_id:
                        print(f"Handshake failed: expected {peer.peer_id}, got {remote_id}")
                        sock.close()
                        continue

                    self.connections[remote_id] = sock

                    print(
                        f"Peer {self.peer_id} makes a connection to Peer {remote_id}"
                    )

                    # Bitfield exchange
                    sock.sendall(encode_bitfield(self.piece_manager.bitfield))
                    print(f"Peer {self.peer_id} sent bitfield ({self.piece_manager.piece_count()} pieces)")

                    msg = recv_message(sock)
                    if msg.msg_type == MessageType.BITFIELD:
                        remote_bitfield = decode_bitfield_payload(msg.payload, self.piece_manager.num_pieces)
                        print(f"Peer {self.peer_id} received bitfield from {remote_id} ({remote_bitfield.piece_count()} pieces)")

                        # Interested / Not Interested
                        has_something_we_need = any(
                            not self.piece_manager.bitfield.has_piece(i) and remote_bitfield.has_piece(i)
                            for i in range(self.piece_manager.num_pieces)
                        )

                        if has_something_we_need:
                            sock.sendall(encode_interested())
                            print(f"Peer {self.peer_id} sending INTERESTED to {remote_id}")
                        else:
                            sock.sendall(encode_not_interested())
                            print(f"Peer {self.peer_id} sending NOT_INTERESTED to {remote_id}")

    def register_incoming_connection(self, conn):
        # Read their handshake first, then reply with ours
        remote_id = handshake.receive(conn)
        handshake.send(conn, self.peer_id)

        self.connections[remote_id] = conn

        print(f"Peer {self.peer_id} is connected from Peer {remote_id}")

        return remote_id

    def get_connection(self, peer_id):
        return self.connections.get(peer_id)

    def remove_connection(self, peer_id):
        if peer_id in self.connections:
            self.connections[peer_id].close()
            del self.connections[peer_id]

    def get_all_connections(self):
        return self.connections.values()