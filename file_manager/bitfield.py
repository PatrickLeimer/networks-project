class Bitfield:

    def __init__(self, num_pieces, has_file=False):
        self.num_pieces = num_pieces

        if has_file:
            self.bits = [1] * num_pieces
        else:
            self.bits = [0] * num_pieces

    def has_piece(self, index):
        return self.bits[index] == 1

    def set_piece(self, index):
        self.bits[index] = 1

    def missing_pieces(self):
        return [i for i, bit in enumerate(self.bits) if bit == 0]

    def piece_count(self):
        return sum(self.bits)

    def is_complete(self):
        return all(self.bits)