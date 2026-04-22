<<<<<<< Updated upstream
import threading
import time
=======
import random
import threading
>>>>>>> Stashed changes

from protocol.encoder import encode_choke, encode_unchoke


class ChokingManager:
<<<<<<< Updated upstream

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
=======
    # Two periodic timers:
    #   * preferred neighbors every UnchokingInterval seconds
    #   * optimistically-unchoked neighbor every OptimisticUnchokingInterval seconds

    def __init__(self, peer_id, connection_manager, piece_manager,
                 unchoking_interval, optimistic_interval, num_preferred, logger=None):
        self.peer_id = peer_id
        self.connection_manager = connection_manager
        self.piece_manager = piece_manager
        self.unchoking_interval = unchoking_interval
        self.optimistic_interval = optimistic_interval
        self.num_preferred = num_preferred
        self.logger = logger

        self.preferred = set()          # peer_ids
        self.optimistic = None          # peer_id or None
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def start(self):
        threading.Thread(target=self._preferred_loop, daemon=True).start()
        threading.Thread(target=self._optimistic_loop, daemon=True).start()

    def stop(self):
        self._stop.set()

    # ---- preferred neighbors ----

    def _preferred_loop(self):
        while not self._stop.wait(self.unchoking_interval):
            try:
                self._select_preferred()
            except Exception as e:
                print(f"ChokingManager preferred loop error: {e}")

    def _select_preferred(self):
        neighbors = self.connection_manager.get_all_neighbors()
        interested = [n for n in neighbors if n.peer_interested]

        # spec: if we have the complete file, pick k randomly among interested
        if self.piece_manager.completed():
            random.shuffle(interested)
            new_preferred = [n for n in interested[:self.num_preferred]]
        else:
            # sort by bytes_downloaded desc, break ties randomly
            random.shuffle(interested)
            interested.sort(key=lambda n: n.bytes_downloaded, reverse=True)
            new_preferred = interested[:self.num_preferred]

        new_preferred_ids = {n.peer_id for n in new_preferred}

        with self._lock:
            old_preferred = set(self.preferred)
            self.preferred = new_preferred_ids

        # always unchoke current optimistic pick too
        kept_unchoked = set(new_preferred_ids)
        if self.optimistic is not None:
            kept_unchoked.add(self.optimistic)

        # apply choke/unchoke
        for n in neighbors:
            should_unchoke = n.peer_id in kept_unchoked
            if should_unchoke and n.am_choking:
                n.am_choking = False
                try:
                    n.send(encode_unchoke())
                except OSError:
                    pass
            elif not should_unchoke and not n.am_choking:
                n.am_choking = True
                try:
                    n.send(encode_choke())
                except OSError:
                    pass

        # reset download counters for next interval
        for n in neighbors:
            n.bytes_downloaded = 0

        # log if preferred set changed
        if self.logger is not None and new_preferred_ids != old_preferred:
            self.logger.change_log_preferred_neighbors(self.peer_id, sorted(new_preferred_ids))

    # ---- optimistic unchoke ----

    def _optimistic_loop(self):
        while not self._stop.wait(self.optimistic_interval):
            try:
                self._select_optimistic()
            except Exception as e:
                print(f"ChokingManager optimistic loop error: {e}")

    def _select_optimistic(self):
        neighbors = self.connection_manager.get_all_neighbors()

        with self._lock:
            preferred = set(self.preferred)

        # candidates: currently choked AND interested AND not a preferred neighbor
        candidates = [
            n for n in neighbors
            if n.peer_interested and n.am_choking and n.peer_id not in preferred
        ]

        if not candidates:
            return

        pick = random.choice(candidates)

        with self._lock:
            self.optimistic = pick.peer_id

        pick.am_choking = False
        try:
            pick.send(encode_unchoke())
        except OSError:
            return

        if self.logger is not None:
            self.logger.change_log_optimistically_unchoked_neighbor(self.peer_id, pick.peer_id)
>>>>>>> Stashed changes
