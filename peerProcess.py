import sys
import json
import os
import shutil
import threading

from config.config_loader import load_common_config, load_peer_info
from file_manager.logger import Logger
from file_manager.piece_manager import PieceManager
from networking.connection_manager import ConnectionManager
from networking.server import TCPServer
from p2p.choking_manager import ChokingManager


def main():

    if len(sys.argv) != 2:
        print("Usage: python peerProcess.py <peer_id>")
        sys.exit(1)

    peer_id = int(sys.argv[1])
    print(f"Starting peer {peer_id}")

    common_path = "Common.cfg" if os.path.exists("Common.cfg") else "local_testing/Common.cfg"
    peers_path = "PeerInfo.cfg" if os.path.exists("PeerInfo.cfg") else "local_testing/PeerInfo.cfg"
    common_cfg = load_common_config(common_path)
    peer_info_list = load_peer_info(peers_path)

    print(f"Common config: {json.dumps(vars(common_cfg), indent=2)}")

    this_peer = next((p for p in peer_info_list if p.peer_id == peer_id), None)
    if this_peer is None:
        print("Peer ID not found in PeerInfo.cfg")
        sys.exit(1)

    _logger = Logger(f"log_peer_{peer_id}.log")

    peer_dir = f"peer_{peer_id}"
    os.makedirs(peer_dir, exist_ok=True)

    if this_peer.has_file:
        src = common_cfg.file_name
        dst = os.path.join(peer_dir, os.path.basename(common_cfg.file_name))
        if os.path.abspath(src) != os.path.abspath(dst) and not os.path.exists(dst):
            shutil.copy(src, dst)

    piece_manager = PieceManager(peer_id, common_cfg, this_peer.has_file)
    print(f"Pieces owned: {piece_manager.piece_count()} / {piece_manager.num_pieces}")

    connection_manager = ConnectionManager(peer_id, peer_info_list, piece_manager, _logger)

    server = TCPServer(peer_id, this_peer.hostname, this_peer.port, connection_manager)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    # outgoing connects to all peers that started before us
    connection_manager.start_outgoing_connections()

    choking_manager = ChokingManager(
        peer_id=peer_id,
        connection_manager=connection_manager,
        piece_manager=piece_manager,
        unchoking_interval=common_cfg.unchoking_interval,
        optimistic_interval=common_cfg.optimistic_unchoking_interval,
        num_preferred=common_cfg.num_preferred_neighbors,
        logger=_logger,
    )
    choking_manager.start()

    # block until everyone (us + all neighbors) has the complete file
    try:
        while True:
            if piece_manager.completed():
                piece_manager.write_file_to_disk()
            if connection_manager.all_peers_complete():
                print(f"Peer {peer_id}: all peers have the complete file. Shutting down.")
                break
            server_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        print(f"Peer {peer_id}: interrupted, shutting down")
    finally:
        choking_manager.stop()
        server.stop()
        connection_manager.shutdown()
        server_thread.join(timeout=2.0)
        _logger.close()


if __name__ == "__main__":
    main()
