import os 
import datetime
import logging

class Logger:

    def __init__(self, log_file):
        self.log_file = log_file
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s', filemode = 'w')

    def log_information(self, message):
        logging.info(message)
    
    def log_warn(self, message):
        logging.warning(message)

    def log_err(self, message):
        logging.error(message)

    def get_timestamp(self):
        now = datetime.datetime.now()
        # timestamp in following format: date, hour, minute, second 
        return now.strftime("%Y-%m-%d %H:%M:%S")

    Logger = logging.getLogger()
    Logger.setLevel(logging.INFO)
    
    def tcp_log_connect(self, peer_id, peer2_id, timestamp):
        # is hte ID of peer who generates the log, peer2_id is the peer connected from peer_id 
        # timestamp in following format: date, hour, minute, second 
        self.log_information(f"{timestamp}: Peer {peer_id} is connected to Peer {peer2_id}.")

    def tcp_failed_connect_log(self, peer_id, peer2_id, timestamp):
        # [Time]: Peer [peer_ID 1] failed to connect to Peer [peer_ID 2].
        self.log_err(f"{timestamp}: Peer {peer_id} failed to connect to Peer {peer2_id}.")

    def change_log_preferred_neighbors(self, peer_id, preferred_neighbors, timestamp):
        # [preferred neighbor list] is the list of peer IDs separated by comma
        self.log_information(f"{timestamp}: Peer {peer_id} has the preferred neighbors {preferred_neighbors}.")

    def change_log_optimistically_unchoked_neighbor(self, peer_id, optimistically_unchoked_neighbor, timestamp):
        # [optimistically unchoked neighbor ID] is the peer ID of the optimistically unchoked neighbor.
        self.log_information(f"{timestamp}: Peer {peer_id} has the optimistically unchoked neighbor {optimistically_unchoked_neighbor}.")

    def unchoking_log(self, peer_id, peer2_id, timestamp): 
        # peer_ID 1] represents the peer who is unchoked and [peer_ID 2] represents the peer who unchokes [peer_ID 1].
        self.log_information(f"{timestamp}: Peer {peer_id} is unchoked by {peer2_id}.")

    def choking_log(self, peer_id, peer2_id, timestamp):
        # [Time]: Peer [peer_ID 1] is choked by [peer_ID 2].
        self.log_err(f"{timestamp}: Peer {peer_id} is choked by {peer2_id}.")

    def rec_have_message_log(self, peer_id, peer2_id, piece_index, timestamp):
        # [piece index] is the index of the piece that is received by [peer_ID 1] from [peer_ID 2].
        self.log_information(f"{timestamp}: Peer {peer_id} received the 'have' message from {peer2_id} for piece {piece_index}.")

    def rec_interested_message_log(self, peer_id, peer2_id, timestamp):
        # [Time]: Peer [peer_ID 1] received the ‘interested’ message from [peer_ID 2].
        self.log_information(f"{timestamp}: Peer {peer_id} received the 'interested' message from {peer2_id}.")
    
    def rec_not_interested_message_log(self, peer_id, peer2_id, timestamp):
        # [Time]: Peer [peer_ID 1] received the ‘not interested’ message from [peer_ID 2].
        self.log_information(f"{timestamp}: Peer {peer_id} received the 'not interested' message from {peer2_id}.")

    def downloading_piece_log(self, peer_id, peer2_id, piece_index, timestamp):
        # [Time]: Peer [peer_ID 1] has downloaded the piece [piece index] from [peer_ID 2]
        self.log_information(f"{timestamp}: Peer {peer_id} downloaded piece {piece_index} from {peer2_id}.")
    
    def complete_download_log(self, peer_id, timestamp):
        # [Time]: Peer [peer_ID] has downloaded the complete file.
        self.log_information(f"{timestamp}: Peer {peer_id} has downloaded the complete file.")