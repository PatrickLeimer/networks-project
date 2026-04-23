import logging
import threading


class Logger:

    def __init__(self, log_file):
        self.log_file = log_file
        self._lock = threading.Lock()

        self._logger = logging.getLogger(f"peer_logger_{id(self)}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        self._logger.handlers.clear()

        file_handler = logging.FileHandler(self.log_file, mode="w", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        self._logger.addHandler(file_handler)
        self._handler = file_handler

    def _write(self, level, message):
        with self._lock:
            self._logger.log(level, message)
            self._handler.flush()

    def log_information(self, message):
        self._write(logging.INFO, message)

    def log_warn(self, message):
        self._write(logging.WARNING, message)

    def log_err(self, message):
        self._write(logging.ERROR, message)

    def tcp_log_connect(self, peer_id, peer2_id):
        # is the ID of peer who generates the log, peer2_id is the peer connected from peer_id
        self.log_information(f"Peer {peer_id} makes a connection to Peer {peer2_id}.")

    def tcp_log_connected_from(self, peer_id, peer2_id):
        # [peer_ID 1] is the ID of peer who generates the log, [peer_ID 2] is the peer who has made TCP connection to [peer_ID 1].
        self.log_information(f"Peer {peer_id} is connected from Peer {peer2_id}.")

    def tcp_failed_connect_log(self, peer_id, peer2_id):
        # [Time]: Peer [peer_ID 1] failed to connect to Peer [peer_ID 2].
        self.log_err(f"Peer {peer_id} failed to connect to Peer {peer2_id}.")

    def change_log_preferred_neighbors(self, peer_id, preferred_neighbors):
        # [preferred neighbor list] is the list of peer IDs separated by comma
        if isinstance(preferred_neighbors, (list, tuple, set)):
            preferred_neighbors = ", ".join(str(neighbor) for neighbor in preferred_neighbors)

        self.log_information(f"Peer {peer_id} has the preferred neighbors {preferred_neighbors}.")

    def change_log_optimistically_unchoked_neighbor(self, peer_id, optimistically_unchoked_neighbor):
        # [optimistically unchoked neighbor ID] is the peer ID of the optimistically unchoked neighbor.
        self.log_information(f"Peer {peer_id} has the optimistically unchoked neighbor {optimistically_unchoked_neighbor}.")

    def unchoking_log(self, peer_id, peer2_id):
        # peer_ID 1] represents the peer who is unchoked and [peer_ID 2] represents the peer who unchokes [peer_ID 1].
        self.log_information(f"Peer {peer_id} is unchoked by {peer2_id}.")

    def choking_log(self, peer_id, peer2_id):
        # [Time]: Peer [peer_ID 1] is choked by [peer_ID 2].
        self.log_information(f"Peer {peer_id} is choked by {peer2_id}.")

    def rec_have_message_log(self, peer_id, peer2_id, piece_index):
        # [piece index] is the piece index contained in the message.
        self.log_information(
            f"Peer {peer_id} received the 'have' message from {peer2_id} for the piece {piece_index}.")

    def rec_interested_message_log(self, peer_id, peer2_id):
        # [Time]: Peer [peer_ID 1] received the ‘interested’ message from [peer_ID 2].
        self.log_information(f"Peer {peer_id} received the 'interested' message from {peer2_id}.")

    def rec_not_interested_message_log(self, peer_id, peer2_id):
        # [Time]: Peer [peer_ID 1] received the ‘not interested’ message from [peer_ID 2].
        self.log_information(f"Peer {peer_id} received the 'not interested' message from {peer2_id}.")

    def downloading_piece_log(self, peer_id, peer2_id, piece_index, piece_count):
        # [Time]: Peer [peer_ID 1] has downloaded the piece [piece index] from [peer_ID 2]
        self.log_information(
            f"Peer {peer_id} has downloaded the piece {piece_index} from {peer2_id}. "
            f"Now the number of pieces it has is {piece_count}.")

    def complete_download_log(self, peer_id):
        # [Time]: Peer [peer_ID] has downloaded the complete file.
        self.log_information(f"Peer {peer_id} has downloaded the complete file.")

    def close(self):
        for handler in list(self._logger.handlers):
            handler.flush()
            handler.close()
            self._logger.removeHandler(handler)
