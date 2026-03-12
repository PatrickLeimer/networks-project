import struct
from protocol.message import Message
from file_manager.bitfield import Bitfield


HANDSHAKE_HEADER = b"P2PFILESHARINGPROJ"
HANDSHAKE_LENGTH = 32

# Read exactly num_bytes from the socket, looping until we have them all
def recv_exactly(sock, num_bytes):
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            raise ConnectionError("Connection closed while reading")
        data += chunk
    return data

# Read and validate a 32 byte handshake from the socket ->returns Peer ID
def decode_handshake(sock):
    data = recv_exactly(sock, HANDSHAKE_LENGTH)

    header = data[:18]
    if header != HANDSHAKE_HEADER:
        raise ValueError(f"Invalid handshake header: {header}")

    # bytes 18-27 are zero bits (we don't need to check them)
    peer_id = struct.unpack(">I", data[28:32])[0]
    return peer_id

# Read a prefixed message from socket -> returns message object
def recv_message(sock):
    # Read the 4-byte message length
    length_data = recv_exactly(sock, 4)
    length = struct.unpack(">I", length_data)[0]

    # Read the rest of the message (type + payload)
    message_data = recv_exactly(sock, length)

    return Message.decode(message_data)

# Extract piece index from having message payload
def decode_have_payload(payload):
    return struct.unpack(">I", payload)[0]

# Unpack bitfield bytes into a Bitfield object 
def decode_bitfield_payload(payload, num_pieces):
    bitfield = Bitfield(num_pieces)

    for i in range(num_pieces):
        byte_index = i // 8
        bit_offset = 7 - (i % 8)

        if payload[byte_index] & (1 << bit_offset):
            bitfield.set_piece(i)

    return bitfield

# Same logic as HAVE but duplicate for readability when called
def decode_request_payload(payload):
    return struct.unpack(">I", payload)[0]

# Extract piece index and data from a piece message payload
def decode_piece_payload(payload):
    piece_index = struct.unpack(">I", payload[:4])[0]
    data = payload[4:]
    return piece_index, data
