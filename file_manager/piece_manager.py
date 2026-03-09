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

    def store_piece(self, index, data):

        if index not in self.pieces:

            self.pieces[index] = data
            self.bitfield.set_piece(index)

    def completed(self):

        return self.bitfield.is_complete()

    def piece_count(self):

        return self.bitfield.piece_count()