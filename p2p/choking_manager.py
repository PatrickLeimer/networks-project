import threading
import time

from protocol.encoder import encode_choke, encode_unchoke


class ChokingManager:

    def __init__(self, peer_id, common_config, connection_manager, piece_manager, logger=None):
        self.peer_id = peer_id
        self.common_config = common_config
        self.connection_manager = connection_manager
        self.piece_manager = piece_manager
        self.logger = logger

        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _run(self):
        while self.running:
            self._run_interval()

            interval = self.common_config.unchoking_interval
            slept = 0.0
            while self.running and slept < interval:
                time.sleep(0.2)
                slept += 0.2

    def _run_interval(self):
        neighbors = self.connection_manager.get_all_neighbors()
        interested_neighbors = [
            neighbor for neighbor in neighbors if neighbor.peer_interested
        ]

        preferred_count = self.common_config.num_preferred_neighbors
        ranked_neighbors = sorted(
            interested_neighbors,
            key=lambda neighbor: (-neighbor.bytes_downloaded, neighbor.peer_id),
        )
        preferred_neighbors = ranked_neighbors[:preferred_count]
        preferred_ids = [neighbor.peer_id for neighbor in preferred_neighbors]

        if self.logger is not None:
            self.logger.change_log_preferred_neighbors(self.peer_id, preferred_ids)

        preferred_set = set(preferred_ids)
        for neighbor in neighbors:
            should_choke = neighbor.peer_id not in preferred_set
            self._apply_choke_state(neighbor, should_choke)
            neighbor.bytes_downloaded = 0

    def _apply_choke_state(self, neighbor, should_choke):
        if should_choke == neighbor.am_choking:
            return

        try:
            if should_choke:
                neighbor.sock.sendall(encode_choke())
            else:
                neighbor.sock.sendall(encode_unchoke())
        except OSError as exc:
            if self.logger is not None:
                self.logger.log_warn(
                    f"Peer {self.peer_id} failed to update choke state for "
                    f"Peer {neighbor.peer_id}: {exc}"
                )
            else:
                print(
                    f"Peer {self.peer_id} failed to update choke state for "
                    f"Peer {neighbor.peer_id}: {exc}"
                )
            return

        neighbor.am_choking = should_choke
