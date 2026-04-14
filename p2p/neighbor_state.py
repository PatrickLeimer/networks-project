import threading

from file_manager.bitfield import Bitfield


class NeighborState:
    """Per-peer view: the socket, their bitfield, choke/interest flags, and a
    byte counter used by the choking manager to pick preferred neighbors."""

    def __init__(self, peer_id: int, sock, num_pieces: int):
        self.peer_id = peer_id
        self.sock = sock
        self.bitfield = Bitfield(num_pieces)

        # choke state is from OUR perspective
        self.am_choking = True          # we are choking them
        self.peer_choking = True        # they are choking us
        self.am_interested = False      # we want something they have
        self.peer_interested = False    # they want something we have

        self.bytes_downloaded = 0       # reset each unchoking interval

        self.send_lock = threading.Lock()

    def send(self, data: bytes):
        with self.send_lock:
            self.sock.sendall(data)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass
