import random
import threading

from protocol.decoder import (
    recv_message,
    decode_bitfield_payload,
    decode_have_payload,
    decode_request_payload,
    decode_piece_payload,
)
<<<<<<< Updated upstream
from protocol.encoder import encode_interested, encode_not_interested, encode_piece
=======
from protocol.encoder import (
    encode_interested,
    encode_not_interested,
    encode_request,
    encode_piece,
    encode_have,
)
>>>>>>> Stashed changes
from protocol.message_types import MessageType


class PeerConnection:
    # Runs one receive loop per neighbor; also drives the request flow
    # (send REQUEST on UNCHOKE, send next REQUEST + broadcast HAVE on PIECE).

    def __init__(self, neighbor, piece_manager, peer_id, connection_manager, logger=None):
        self.neighbor = neighbor
        self.piece_manager = piece_manager
<<<<<<< Updated upstream
        self.peer_id = peer_id  # our id, just for prints
=======
        self.peer_id = peer_id
>>>>>>> Stashed changes
        self.connection_manager = connection_manager
        self.logger = logger

        self.running = False
        self.thread = None
        self.requested_piece_index = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
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
            # if we had an outstanding request to this peer, release it
            if self.neighbor.pending_request is not None:
                self.piece_manager.release_piece(self.neighbor.pending_request)
                self.neighbor.pending_request = None

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
            self._on_have(decode_have_payload(msg.payload))
        elif mt == MessageType.BITFIELD:
            self._on_bitfield(
                decode_bitfield_payload(msg.payload, self.piece_manager.num_pieces)
            )
        elif mt == MessageType.REQUEST:
            self._on_request(decode_request_payload(msg.payload))
        elif mt == MessageType.PIECE:
            piece_index, data = decode_piece_payload(msg.payload)
            self._on_piece(piece_index, data)
        else:
            print(f"Peer {self.peer_id}: unknown message type {mt} from {self.neighbor.peer_id}")

    # ---- handlers ----

    def _on_choke(self):
        self.neighbor.peer_choking = True
        if self.requested_piece_index is not None:
            self.piece_manager.clear_requested_piece(self.requested_piece_index)
            self.requested_piece_index = None

        if self.logger is not None:
            self.logger.choking_log(self.peer_id, self.neighbor.peer_id)
        # release any outstanding request so another peer can fill it
        if self.neighbor.pending_request is not None:
            self.piece_manager.release_piece(self.neighbor.pending_request)
            self.neighbor.pending_request = None

    def _on_unchoke(self):
        self.neighbor.peer_choking = False
        if self.logger is not None:
            self.logger.unchoking_log(self.peer_id, self.neighbor.peer_id)
<<<<<<< Updated upstream
        else:
            print(f"Peer {self.peer_id} is unchoked by {self.neighbor.peer_id}")
=======
>>>>>>> Stashed changes
        self._request_next_piece()

    def _on_interested(self):
        self.neighbor.peer_interested = True
        if self.logger is not None:
            self.logger.rec_interested_message_log(self.peer_id, self.neighbor.peer_id)

    def _on_not_interested(self):
        self.neighbor.peer_interested = False
        if self.logger is not None:
            self.logger.rec_not_interested_message_log(self.peer_id, self.neighbor.peer_id)

    def _on_have(self, piece_index):
        self.neighbor.bitfield.set_piece(piece_index)
        self.connection_manager.update_peer_completion(
            self.neighbor.peer_id,
            self.neighbor.bitfield.is_complete(),
        )
        if self.logger is not None:
            self.logger.rec_have_message_log(self.peer_id, self.neighbor.peer_id, piece_index)

        if not self.piece_manager.bitfield.has_piece(piece_index):
            if not self.neighbor.am_interested:
                self.neighbor.am_interested = True
                try:
                    self.neighbor.send(encode_interested())
                except OSError:
                    return

        # if everyone's done, let peerProcess know
        self.connection_manager.check_global_completion()

            if not self.neighbor.peer_choking and self.requested_piece_index is None:
                self._request_next_piece()

    def _on_bitfield(self, remote_bitfield):
        self.neighbor.bitfield = remote_bitfield
<<<<<<< Updated upstream
        self.connection_manager.update_peer_completion(
            self.neighbor.peer_id,
            remote_bitfield.is_complete(),
        )
        print(f"Peer {self.peer_id} received BITFIELD from {self.neighbor.peer_id}")
=======
>>>>>>> Stashed changes
        self._reevaluate_interest()
        self.connection_manager.check_global_completion()

    def _on_request(self, piece_index):
<<<<<<< Updated upstream
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

=======
        # only serve pieces if we're not choking them
        if self.neighbor.am_choking:
            return
        data = self.piece_manager.get_piece(piece_index)
        if data is None:
            return
        try:
            self.neighbor.send(encode_piece(piece_index, data))
        except OSError:
            pass

    def _on_piece(self, piece_index, data):
        # only accept if we asked for this piece from this peer
        if self.neighbor.pending_request != piece_index:
            return
        self.neighbor.pending_request = None
>>>>>>> Stashed changes
        self.neighbor.bytes_downloaded += len(data)

        already_had = self.piece_manager.bitfield.has_piece(piece_index)
        self.piece_manager.store_piece(piece_index, data)

        if not already_had:
            piece_count = self.piece_manager.piece_count()
            if self.logger is not None:
                self.logger.downloading_piece_log(
                    self.peer_id,
                    self.neighbor.peer_id,
                    piece_index,
                    piece_count,
                )

            # broadcast HAVE to every neighbor
            self.connection_manager.broadcast_have(piece_index)

            if self.piece_manager.completed():
<<<<<<< Updated upstream
                self.connection_manager.mark_self_complete()
                self.logger.complete_download_log(self.peer_id)
        else:
            print(
                f"Peer {self.peer_id} downloaded piece {piece_index} from "
                f"{self.neighbor.peer_id} (now has {piece_count})"
            )
            if self.piece_manager.completed():
                self.connection_manager.mark_self_complete()

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
=======
                self.piece_manager.write_to_disk()
                if self.logger is not None:
                    self.logger.complete_download_log(self.peer_id)
                # re-evaluate interest on everyone (we might no longer want pieces)
                self.connection_manager.reevaluate_all_interest()
                self.connection_manager.check_global_completion()

        # request the next piece from this peer if they're still unchoking us
        self._request_next_piece()

    def _reevaluate_interest(self):
>>>>>>> Stashed changes
        wants_something = False
        for i in range(self.piece_manager.num_pieces):
            if neighbor.bitfield.has_piece(i) and not self.piece_manager.bitfield.has_piece(i):
                wants_something = True
                break

<<<<<<< Updated upstream
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
=======
        try:
            if wants_something and not self.neighbor.am_interested:
                self.neighbor.am_interested = True
                self.neighbor.send(encode_interested())
            elif not wants_something and self.neighbor.am_interested:
                self.neighbor.am_interested = False
                self.neighbor.send(encode_not_interested())
        except OSError:
            pass

    def _request_next_piece(self):
        # Pick a random piece the neighbor has that we don't have and no one else
        # is currently fetching; send REQUEST. Spec uses random selection, not rarest-first.
        if self.neighbor.peer_choking:
            return
        if self.neighbor.pending_request is not None:
            return
        if self.piece_manager.completed():
            return

        candidates = []
        for i in range(self.piece_manager.num_pieces):
            if (self.neighbor.bitfield.has_piece(i)
                    and not self.piece_manager.bitfield.has_piece(i)
                    and i not in self.piece_manager.pending_requests):
                candidates.append(i)

        if not candidates:
            return

        piece_index = random.choice(candidates)
        if not self.piece_manager.reserve_piece(piece_index):
            return

        self.neighbor.pending_request = piece_index
        try:
            self.neighbor.send(encode_request(piece_index))
        except OSError:
            self.piece_manager.release_piece(piece_index)
            self.neighbor.pending_request = None
>>>>>>> Stashed changes
