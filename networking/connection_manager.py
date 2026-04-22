from networking.client import connect_to_peer
from protocol import handshake
from protocol.encoder import (
    encode_bitfield,
    encode_have,
    encode_interested,
    encode_not_interested,
    encode_request,
)
from protocol.decoder import recv_message, decode_bitfield_payload
from protocol.message_types import MessageType

from p2p.neighbor_state import NeighborState
from p2p.peer_connection import PeerConnection


class ConnectionManager:

    def __init__(self, peer_id, peer_info_list, piece_manager, logger=None):

        self.peer_id = peer_id
        self.peer_info_list = peer_info_list
        self.piece_manager = piece_manager
        self.logger = logger
        self.peer_completion = {
            peer.peer_id: bool(peer.has_file) for peer in peer_info_list
        }
        self.peer_completion[self.peer_id] = self.piece_manager.completed()

        # peer_id -> NeighborState
        self.neighbors = {}

        # peer_id -> PeerConnection (receive loop)
        self.peer_connections = {}

    def start_outgoing_connections(self):

        for peer in self.peer_info_list:

            # only connect to peers with smaller ID so there's just one connection per pair

            if peer.peer_id < self.peer_id:

                try:
                    sock = connect_to_peer(peer.hostname, peer.port)
                except OSError:
                    if self.logger is not None:
                        self.logger.tcp_failed_connect_log(self.peer_id, peer.peer_id)
                    continue

                if sock:
                    # send our id, then read theirs to confirm who answered
                    handshake.send(sock, self.peer_id)
                    remote_id = handshake.receive(sock)

                    if remote_id != peer.peer_id:
                        print(f"Handshake failed: expected {peer.peer_id}, got {remote_id}")
                        sock.close()
                        continue

                    if self.logger is not None:
                        self.logger.tcp_log_connect(self.peer_id, remote_id)
                    else:
                        print(f"Peer {self.peer_id} makes a connection to Peer {remote_id}")

                    self._setup_neighbor(sock, remote_id)

    def register_incoming_connection(self, conn):
        # read their handshake first, then reply with ours
        remote_id = handshake.receive(conn)
        handshake.send(conn, self.peer_id)

        if self.logger is not None:
            self.logger.tcp_log_connected_from(self.peer_id, remote_id)
        else:
            print(f"Peer {self.peer_id} is connected from Peer {remote_id}")

        self._setup_neighbor(conn, remote_id)

        return remote_id

    # Called on both sides right after handshake. Creates the NeighborState,
    # does the bitfield + initial interested exchange, then starts the
    # persistent receive loop.
    def _setup_neighbor(self, sock, remote_id):

        neighbor = NeighborState(remote_id, sock, self.piece_manager.num_pieces)
        self.neighbors[remote_id] = neighbor

        # send our bitfield
        sock.sendall(encode_bitfield(self.piece_manager.bitfield))
        print(
            f"Peer {self.peer_id} sent bitfield to {remote_id} "
            f"({self.piece_manager.piece_count()} pieces)"
        )

        # receive theirs (spec says BITFIELD is always the first message after
        # handshake, so read it synchronously before starting the loop)
        msg = recv_message(sock)
        if msg.msg_type == MessageType.BITFIELD:
            remote_bitfield = decode_bitfield_payload(
                msg.payload, self.piece_manager.num_pieces
            )
            neighbor.bitfield = remote_bitfield
            self.update_peer_completion(remote_id, remote_bitfield.is_complete())
            print(
                f"Peer {self.peer_id} received bitfield from {remote_id} "
                f"({remote_bitfield.piece_count()} pieces)"
            )
        else:
            print(f"Peer {self.peer_id}: expected BITFIELD from {remote_id}, got {msg.msg_type}")

        # send INTERESTED or NOT_INTERESTED based on what they have
        has_something_we_need = False
        for i in range(self.piece_manager.num_pieces):
            if neighbor.bitfield.has_piece(i) and not self.piece_manager.bitfield.has_piece(i):
                has_something_we_need = True
                break

        if has_something_we_need:
            neighbor.am_interested = True
            sock.sendall(encode_interested())
            print(f"Peer {self.peer_id} sending INTERESTED to {remote_id}")
        else:
            neighbor.am_interested = False
            sock.sendall(encode_not_interested())
            print(f"Peer {self.peer_id} sending NOT_INTERESTED to {remote_id}")

        # kick off the receive loop for the rest of this peer's lifetime
        pc = PeerConnection(
            neighbor,
            self.piece_manager,
            self.peer_id,
            self,
            self.logger,
        )
        self.peer_connections[remote_id] = pc
        pc.start()

    def send_request(self, neighbor, piece_index):
        neighbor.sock.sendall(encode_request(piece_index))

    def broadcast_have(self, piece_index):
        message = encode_have(piece_index)

        for neighbor in self.get_all_neighbors():
            neighbor.sock.sendall(message)

    def get_neighbor(self, peer_id):
        return self.neighbors.get(peer_id)

    def get_all_neighbors(self):
        return list(self.neighbors.values())

    def update_peer_completion(self, peer_id, is_complete):
        self.peer_completion[peer_id] = is_complete

    def mark_self_complete(self):
        self.peer_completion[self.peer_id] = self.piece_manager.completed()

    def all_peers_complete(self):
        if not self.piece_manager.completed():
            self.peer_completion[self.peer_id] = False
            return False

        self.peer_completion[self.peer_id] = True
        return all(self.peer_completion.get(peer.peer_id, False) for peer in self.peer_info_list)

    def shutdown(self):
        for peer_id in list(self.peer_connections.keys()):
            self.remove_connection(peer_id)

    def remove_connection(self, peer_id):
        if peer_id in self.peer_connections:
            self.peer_connections[peer_id].stop()
            del self.peer_connections[peer_id]

        if peer_id in self.neighbors:
            self.neighbors[peer_id].close()
            del self.neighbors[peer_id]
