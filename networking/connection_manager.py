import threading

from networking.client import connect_to_peer
from protocol import handshake
from protocol.encoder import (
    encode_bitfield,
    encode_have,
    encode_interested,
    encode_not_interested,
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

        self.neighbors = {}
        self.peer_connections = {}
        self._lock = threading.Lock()

        # signaled when every peer (including us) reports a complete bitfield
        self.all_done = threading.Event()

        # expected peer count (everyone else in PeerInfo.cfg)
        self._expected_peers = {p.peer_id for p in peer_info_list if p.peer_id != peer_id}

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
                    handshake.send(sock, self.peer_id)
                    remote_id = handshake.receive(sock)

                    if remote_id != peer.peer_id:
                        print(f"Handshake failed: expected {peer.peer_id}, got {remote_id}")
                        sock.close()
                        continue

                    if self.logger is not None:
                        self.logger.tcp_log_connect(self.peer_id, remote_id)

                    self._setup_neighbor(sock, remote_id)

    def register_incoming_connection(self, conn):
        remote_id = handshake.receive(conn)
        handshake.send(conn, self.peer_id)

        if self.logger is not None:
            self.logger.tcp_log_connected_from(self.peer_id, remote_id)

        self._setup_neighbor(conn, remote_id)
        return remote_id

    def _setup_neighbor(self, sock, remote_id):

        neighbor = NeighborState(remote_id, sock, self.piece_manager.num_pieces)
        with self._lock:
            self.neighbors[remote_id] = neighbor

        # send our bitfield if we have anything
        if self.piece_manager.piece_count() > 0:
            neighbor.send(encode_bitfield(self.piece_manager.bitfield))

        # receive theirs (spec allows peer to skip BITFIELD if they have nothing)
        msg = recv_message(sock)
        first_non_bitfield = None
        if msg.msg_type == MessageType.BITFIELD:
            remote_bitfield = decode_bitfield_payload(
                msg.payload, self.piece_manager.num_pieces
            )
            neighbor.bitfield = remote_bitfield
        else:
            first_non_bitfield = msg

        # send INTERESTED or NOT_INTERESTED
        has_something_we_need = False
        for i in range(self.piece_manager.num_pieces):
            if neighbor.bitfield.has_piece(i) and not self.piece_manager.bitfield.has_piece(i):
                has_something_we_need = True
                break

        if has_something_we_need:
            neighbor.am_interested = True
            neighbor.send(encode_interested())
        else:
            neighbor.am_interested = False
            neighbor.send(encode_not_interested())

        pc = PeerConnection(neighbor, self.piece_manager, self.peer_id, self, self.logger)
        with self._lock:
            self.peer_connections[remote_id] = pc
        # if the peer skipped BITFIELD, dispatch whatever we received instead
        if first_non_bitfield is not None:
            pc._dispatch(first_non_bitfield)
        pc.start()

        # if everyone showed up and everyone's complete, we may be done already
        self.check_global_completion()

    def get_neighbor(self, peer_id):
        return self.neighbors.get(peer_id)

    def get_all_neighbors(self):
        with self._lock:
            return list(self.neighbors.values())

    def shutdown(self):
        for peer_id in list(self.peer_connections.keys()):
            self.remove_connection(peer_id)

    def remove_connection(self, peer_id):
        with self._lock:
            if peer_id in self.peer_connections:
                self.peer_connections[peer_id].stop()
                del self.peer_connections[peer_id]

            if peer_id in self.neighbors:
                self.neighbors[peer_id].close()
                del self.neighbors[peer_id]

    # ---- helpers used by PeerConnection + ChokingManager ----

    def broadcast_have(self, piece_index):
        msg = encode_have(piece_index)
        for neighbor in self.get_all_neighbors():
            try:
                neighbor.send(msg)
            except OSError:
                continue

    def reevaluate_all_interest(self):
        for neighbor in self.get_all_neighbors():
            wants_something = False
            for i in range(self.piece_manager.num_pieces):
                if neighbor.bitfield.has_piece(i) and not self.piece_manager.bitfield.has_piece(i):
                    wants_something = True
                    break
            try:
                if wants_something and not neighbor.am_interested:
                    neighbor.am_interested = True
                    neighbor.send(encode_interested())
                elif not wants_something and neighbor.am_interested:
                    neighbor.am_interested = False
                    neighbor.send(encode_not_interested())
            except OSError:
                continue

    def check_global_completion(self):
        if not self.piece_manager.completed():
            return
        neighbors = self.get_all_neighbors()
        # must have connected to all expected peers
        connected_ids = {n.peer_id for n in neighbors}
        if connected_ids != self._expected_peers:
            return
        # every neighbor's bitfield must also be complete
        for n in neighbors:
            if not n.bitfield.is_complete():
                return
        self.all_done.set()
