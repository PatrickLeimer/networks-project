import struct
import math
from protocol.message import Message
from protocol.message_types import MessageType


HANDSHAKE_HEADER = b"P2PFILESHARINGPROJ"
HANDSHAKE_ZERO_BITS = b"\x00" * 10


def encode_handshake(peer_id):
    # 18 byte header + 10 zero bytes + 4 byte = 32 bytes
    return HANDSHAKE_HEADER + HANDSHAKE_ZERO_BITS + struct.pack(">I", peer_id)

def encode_choke():
    return Message(MessageType.CHOKE).encode()

def encode_unchoke():
    return Message(MessageType.UNCHOKE).encode()

def encode_interested():
    return Message(MessageType.INTERESTED).encode()

def encode_not_interested():
    return Message(MessageType.NOT_INTERESTED).encode()

def encode_have(piece_index):
    payload = struct.pack(">I", piece_index)
    return Message(MessageType.HAVE, payload).encode()

def encode_bitfield(bitfield):
    num_bytes = math.ceil(bitfield.num_pieces / 8)
    packed = bytearray(num_bytes)

    for i in range(bitfield.num_pieces):
        if bitfield.bits[i] == 1:
            byte_index = i // 8
            bit_offset = 7 - (i % 8)
            packed[byte_index] |= (1 << bit_offset)

    return Message(MessageType.BITFIELD, bytes(packed)).encode()

def encode_request(piece_index):
    payload = struct.pack(">I", piece_index)
    return Message(MessageType.REQUEST, payload).encode()


def encode_piece(piece_index, data):
    payload = struct.pack(">I", piece_index) + data
    return Message(MessageType.PIECE, payload).encode()
