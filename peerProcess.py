import sys
import json

from config.config_loader import load_common_config, load_peer_info


def main():

    if len(sys.argv) != 2:
        print("Usage: python peerProcess.py <peer_id>")
        sys.exit(1)

    peer_id = int(sys.argv[1])

    print(f"Starting peer {peer_id}")

    # load configs
    common_cfg = load_common_config("local_testing/Common.cfg")
    peer_info_list = load_peer_info("local_testing/PeerInfo.cfg")

    print(f"Common config: {json.dumps(vars(common_cfg), indent=2)}")
    print(f"Peer info: {json.dumps([vars(p) for p in peer_info_list], indent=2)}")


    # find our peer entry
    this_peer = None
    for p in peer_info_list:
        if p.peer_id == peer_id:
            this_peer = p
            break

    if this_peer is None:
        print("Peer ID not found in PeerInfo.cfg")
        sys.exit(1)


if __name__ == "__main__":
    main()