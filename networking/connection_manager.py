from networking.client import connect_to_peer


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
                    self.connections[peer.peer_id] = sock

                    print(
                        f"Peer {self.peer_id} makes a connection to Peer {peer.peer_id}"
                    )

    def register_incoming_connection(self, conn):
        """
        Register a new incoming socket connection.
        The real peer_id will be set after handshake.
        """

        temp_id = f"pending_{id(conn)}"
        self.connections[temp_id] = conn

    def set_peer_id_for_connection(self, temp_id, peer_id):
        """
        After handshake we replace the temporary ID
        with the real peer_id.
        """

        conn = self.connections.pop(temp_id)
        self.connections[peer_id] = conn

    def get_connection(self, peer_id):
        return self.connections.get(peer_id)

    def remove_connection(self, peer_id):
        if peer_id in self.connections:
            self.connections[peer_id].close()
            del self.connections[peer_id]

    def get_all_connections(self):
        return self.connections.values()