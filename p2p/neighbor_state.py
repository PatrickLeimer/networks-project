import threading

from file_manager.bitfield import Bitfield


class NeighborState:

    def __init__(self, peer_id, sock, num_pieces):
        self.peer_id = peer_id
        self.sock = sock
        self.bitfield = Bitfield(num_pieces)

        # choke/interest state (from our perspective)
        self.am_choking = True
        self.peer_choking = True
        self.am_interested = False
        self.peer_interested = False

        # bytes we downloaded FROM this peer in the current unchoking interval
        # (choking manager resets this every p seconds to pick preferred neighbors)
        self.bytes_downloaded = 0

        # piece_index we've asked this peer for and not yet received; spec says
        # at most one outstanding request per peer at a time
        self.pending_request = None

        # serializes sends so choking-manager and receive-loop don't interleave
        self.send_lock = threading.Lock()

    def send(self, data):
        with self.send_lock:
            self.sock.sendall(data)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass
