import struct
# Handshake format (32 bytes total):
#   [18 bytes: header string]
#   [10 bytes: zeros]
#   [4 bytes:  peer_id as unsigned int, big-endian]

HEADER = b"P2PFILESHARINGPROJ"  # exactly 18 bytes
HANDSHAKE_LEN = 32


def encode(peer_id: int) -> bytes:
    # Pack: 18s = 18-byte string, 10x = 10 zero bytes, I = unsigned int
    return struct.pack(">18s10xI", HEADER, peer_id)


def decode(data: bytes) -> int:
    # Unpack just the header and peer_id (skip the 10 zero bytes)
    header, peer_id = struct.unpack(">18s10xI", data)

    if header != HEADER:
        raise ValueError(f"Bad handshake header: {header}")

    return peer_id


def send(sock, peer_id: int):
    sock.sendall(encode(peer_id))


def receive(sock) -> int:
    # Read exactly 32 bytes — blocks until full message arrives
    data = b""
    while len(data) < HANDSHAKE_LEN:
        chunk = sock.recv(HANDSHAKE_LEN - len(data))
        if not chunk:
            raise ConnectionError("Connection closed during handshake")
        data += chunk

    return decode(data)
