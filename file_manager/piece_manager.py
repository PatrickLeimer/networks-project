import os
from file_manager.bitfield import Bitfield


class PieceManager:

    def __init__(self, peer_id, common_config, has_file):

        self.peer_id = peer_id
        self.file_name = common_config.file_name
        self.file_size = common_config.file_size
        self.piece_size = common_config.piece_size
        self.num_pieces = common_config.num_pieces

        self.directory = f"peer_{peer_id}"

        self.bitfield = Bitfield(self.num_pieces, has_file)

        self.pieces = {}
        self.requested_pieces = set()
        self._flushed = has_file

        if has_file:
            self._load_full_file()

    def _load_full_file(self):

        path = self.file_name

        with open(path, "rb") as f:
            data = f.read()

        for i in range(self.num_pieces):

            start = i * self.piece_size
            end = start + self.piece_size

            self.pieces[i] = data[start:end]

    def get_piece(self, index):
        return self.pieces.get(index)

    def reserve_piece(self, index):
        # Atomically mark a piece as pending; returns True if we got the reservation,
        # False if another peer already has it pending or we already have it.
        with self._lock:
            if self.bitfield.has_piece(index) or index in self.pending_requests:
                return False
            self.pending_requests.add(index)
            return True

    def release_piece(self, index):
        # Called when a request failed (peer choked us before sending) so another
        # peer can be asked for this piece later.
        with self._lock:
            self.pending_requests.discard(index)

    def store_piece(self, index, data):
        with self._lock:
            if index not in self.pieces:
                self.pieces[index] = data
                self.bitfield.set_piece(index)
            self.pending_requests.discard(index)

    def completed(self):
        return self.bitfield.is_complete()

    def piece_count(self):
        return self.bitfield.piece_count()

    def write_file_to_disk(self):

        if self._flushed:
            return

        if not self.bitfield.is_complete():
            return

        basename = os.path.basename(self.file_name)
        out_path = os.path.join(self.directory, basename)

        bytes_remaining = self.file_size

        with open(out_path, "wb") as f:
            for i in range(self.num_pieces):
                piece = self.pieces[i]
                write_len = min(len(piece), bytes_remaining)
                f.write(piece[:write_len])
                bytes_remaining -= write_len

        self._flushed = True
