import threading

from protocol.decoder import (
    recv_message,
    decode_bitfield_payload,
    decode_have_payload,
    decode_request_payload,
    decode_piece_payload,
)
from protocol.encoder import encode_interested, encode_not_interested, encode_piece
from protocol.message_types import MessageType


# Runs one receive loop per neighbor, reading length-prefixed messages off
# the socket and updating NeighborState / piece_manager. Sending choke/unchoke,
# request, piece, and have is done by other modules that own those flows.
class PeerConnection:

    def __init__(self, neighbor, piece_manager, peer_id, connection_manager, logger=None):
        self.neighbor = neighbor
        self.piece_manager = piece_manager
        self.peer_id = peer_id  # our id, just for prints
        self.connection_manager = connection_manager
        self.logger = logger

        self.running = False
        self.thread = None
        self.requested_piece_index = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.neighbor.close()

    def _run(self):
        remote_id = self.neighbor.peer_id

        try:
            while self.running:
                msg = recv_message(self.neighbor.sock)
                self._dispatch(msg)

        except (ConnectionError, OSError) as e:
            if self.running:
                print(f"Peer {self.peer_id}: connection to {remote_id} closed ({e})")

        finally:
            self.running = False

    def _dispatch(self, msg):
        mt = msg.msg_type

        if mt == MessageType.CHOKE:
            self._on_choke()

        elif mt == MessageType.UNCHOKE:
            self._on_unchoke()

        elif mt == MessageType.INTERESTED:
            self._on_interested()

        elif mt == MessageType.NOT_INTERESTED:
            self._on_not_interested()

        elif mt == MessageType.HAVE:
            piece_index = decode_have_payload(msg.payload)
            self._on_have(piece_index)

        elif mt == MessageType.BITFIELD:
            remote_bitfield = decode_bitfield_payload(
                msg.payload, self.piece_manager.num_pieces
            )
            self._on_bitfield(remote_bitfield)

        elif mt == MessageType.REQUEST:
            piece_index = decode_request_payload(msg.payload)
            self._on_request(piece_index)

        elif mt == MessageType.PIECE:
            piece_index, data = decode_piece_payload(msg.payload)
            self._on_piece(piece_index, data)

        else:
            print(f"Peer {self.peer_id}: unknown message type {mt} from {self.neighbor.peer_id}")

    # ---- handlers ----
    # Most handlers just update state. Choking manager and request/piece flow
    # are separate modules and will plug in where the TODOs are below.

    def _on_choke(self):
        self.neighbor.peer_choking = True
        if self.requested_piece_index is not None:
            self.piece_manager.clear_requested_piece(self.requested_piece_index)
            self.requested_piece_index = None

        if self.logger is not None:
            self.logger.choking_log(self.peer_id, self.neighbor.peer_id)
        else:
            print(f"Peer {self.peer_id} is choked by {self.neighbor.peer_id}")

    def _on_unchoke(self):
        self.neighbor.peer_choking = False
        if self.logger is not None:
            self.logger.unchoking_log(self.peer_id, self.neighbor.peer_id)
        else:
            print(f"Peer {self.peer_id} is unchoked by {self.neighbor.peer_id}")
        self._request_next_piece()

    def _on_interested(self):
        self.neighbor.peer_interested = True
        if self.logger is not None:
            self.logger.rec_interested_message_log(self.peer_id, self.neighbor.peer_id)
        else:
            print(f"Peer {self.peer_id} received INTERESTED from {self.neighbor.peer_id}")

    def _on_not_interested(self):
        self.neighbor.peer_interested = False
        if self.logger is not None:
            self.logger.rec_not_interested_message_log(self.peer_id, self.neighbor.peer_id)
        else:
            print(f"Peer {self.peer_id} received NOT_INTERESTED from {self.neighbor.peer_id}")

    def _on_have(self, piece_index):
        self.neighbor.bitfield.set_piece(piece_index)
        if self.logger is not None:
            self.logger.rec_have_message_log(self.peer_id, self.neighbor.peer_id, piece_index)
        else:
            print(f"Peer {self.peer_id} received HAVE({piece_index}) from {self.neighbor.peer_id}")

        # if this is a piece we don't have, we might newly be interested
        if not self.piece_manager.bitfield.has_piece(piece_index):
            if not self.neighbor.am_interested:
                self.neighbor.am_interested = True
                self.neighbor.sock.sendall(encode_interested())

            if not self.neighbor.peer_choking and self.requested_piece_index is None:
                self._request_next_piece()

    def _on_bitfield(self, remote_bitfield):
        # normally BITFIELD only comes right after handshake, but if we get
        # another one just overwrite so state stays consistent
        self.neighbor.bitfield = remote_bitfield
        print(f"Peer {self.peer_id} received BITFIELD from {self.neighbor.peer_id}")
        self._reevaluate_interest()

    def _on_request(self, piece_index):
        print(f"Peer {self.peer_id} received REQUEST({piece_index}) from {self.neighbor.peer_id}")
        if self.neighbor.am_choking:
            print(
                f"Peer {self.peer_id} ignoring REQUEST({piece_index}) from "
                f"{self.neighbor.peer_id} because the peer is choked"
            )
            return

        piece_data = self.piece_manager.get_piece(piece_index)
        if piece_data is None:
            print(
                f"Peer {self.peer_id} ignoring REQUEST({piece_index}) from "
                f"{self.neighbor.peer_id} because the piece is unavailable"
            )
            return

        self.neighbor.sock.sendall(encode_piece(piece_index, piece_data))
        print(
            f"Peer {self.peer_id} sent PIECE({piece_index}) to {self.neighbor.peer_id}"
        )

    def _on_piece(self, piece_index, data):
        if self.requested_piece_index == piece_index:
            self.requested_piece_index = None
        else:
            self.piece_manager.clear_requested_piece(piece_index)

        self.neighbor.bytes_downloaded += len(data)
        self.piece_manager.store_piece(piece_index, data)

        piece_count = self.piece_manager.piece_count()
        if self.logger is not None:
            self.logger.downloading_piece_log(
                self.peer_id,
                self.neighbor.peer_id,
                piece_index,
                piece_count,
            )
            if self.piece_manager.completed():
                self.logger.complete_download_log(self.peer_id)
        else:
            print(
                f"Peer {self.peer_id} downloaded piece {piece_index} from "
                f"{self.neighbor.peer_id} (now has {piece_count})"
            )

        self.connection_manager.broadcast_have(piece_index)

        for other_neighbor in self.connection_manager.get_all_neighbors():
            if other_neighbor.peer_id != self.neighbor.peer_id:
                self._reevaluate_interest_for(other_neighbor)

        self._reevaluate_interest()

        if not self.piece_manager.completed() and not self.neighbor.peer_choking:
            self._request_next_piece()

    def _reevaluate_interest(self):
        self._reevaluate_interest_for(self.neighbor)

    def _reevaluate_interest_for(self, neighbor):
        # are any of their pieces ones we don't have?
        wants_something = False
        for i in range(self.piece_manager.num_pieces):
            if neighbor.bitfield.has_piece(i) and not self.piece_manager.bitfield.has_piece(i):
                wants_something = True
                break

        if wants_something and not neighbor.am_interested:
            neighbor.am_interested = True
            neighbor.sock.sendall(encode_interested())

        elif not wants_something and neighbor.am_interested:
            neighbor.am_interested = False
            neighbor.sock.sendall(encode_not_interested())

    def _request_next_piece(self):
        if self.requested_piece_index is not None:
            return

        piece_index = self.piece_manager.choose_missing_piece_from(self.neighbor.bitfield)
        if piece_index is None:
            return

        self.connection_manager.send_request(self.neighbor, piece_index)
        self.requested_piece_index = piece_index
        print(
            f"Peer {self.peer_id} sent REQUEST({piece_index}) to {self.neighbor.peer_id}"
        )
