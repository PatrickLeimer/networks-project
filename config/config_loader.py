class CommonConfig:

    def __init__(self, num_pref, unchoke_interval, opt_interval, file_name, file_size, piece_size):
        self.num_preferred_neighbors = num_pref
        self.unchoking_interval = unchoke_interval
        self.optimistic_unchoking_interval = opt_interval
        self.file_name = file_name
        self.file_size = file_size
        self.piece_size = piece_size



class PeerInfo:

    def __init__(self, peer_id, hostname, port, has_file):
        self.peer_id = peer_id
        self.hostname = hostname
        self.port = port
        self.has_file = has_file



def load_common_config(path):

    config = {}

    with open(path, "r") as f:
        for line in f:
            key, value = line.strip().split()
            config[key] = value

    return CommonConfig(
        int(config["NumberOfPreferredNeighbors"]),
        int(config["UnchokingInterval"]),
        int(config["OptimisticUnchokingInterval"]),
        config["FileName"],
        int(config["FileSize"]),
        int(config["PieceSize"])
    )


def load_peer_info(path):

    peers = []

    with open(path, "r") as f:
        for line in f:
            peer_id, hostname, port, has_file = line.strip().split()

            peers.append(
                PeerInfo(
                    int(peer_id),
                    hostname,
                    int(port),
                    int(has_file)
                )
            )

    return peers