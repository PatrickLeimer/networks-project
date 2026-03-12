from networking.client import connect_to_peer
from protocol import handshake


class ConnectionManager:

    def __init__(self, peer_id, peer_info_list):

        self.peer_id = peer_id
        self.peer_info_list = peer_info_list

        # peer_id -> socket
        self.connections = {}

    def start_outgoing_connections(self):

        for peer in self.peer_info_list:

            # only connect to peers with smaller ID to have 1 connection between each pair
            
            if peer.peer_id < self.peer_id:

                sock = connect_to_peer(peer.hostname, peer.port)

                if sock:
                    # Send our ID, then read theirs to confirm who answered
                    handshake.send(sock, self.peer_id)
                    remote_id = handshake.receive(sock)

                    self.connections[remote_id] = sock

                    print(
                        f"Peer {self.peer_id} makes a connection to Peer {remote_id}"
                    )

    def register_incoming_connection(self, conn):
        # Read their handshake first, then reply with ours
        remote_id = handshake.receive(conn)
        handshake.send(conn, self.peer_id)

        self.connections[remote_id] = conn

        print(f"Peer {self.peer_id} is connected from Peer {remote_id}")

    def get_connection(self, peer_id):
        return self.connections.get(peer_id)

    def remove_connection(self, peer_id):
        if peer_id in self.connections:
            self.connections[peer_id].close()
            del self.connections[peer_id]

    def get_all_connections(self):
        return self.connections.values()