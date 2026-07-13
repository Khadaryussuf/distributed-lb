class ConsistentHashMap:
    def __init__(self, num_slots=512, num_virtual_servers=9):
        self.num_slots = num_slots
        self.num_virtual_servers = num_virtual_servers
        
        # The circle itself: an array where each index is a "slot".
        # None means empty. Otherwise, it holds the server's ID.
        self.slots = [None] * num_slots
        
        # Keeps track of which slots belong to which server,
        # so we can easily remove a server later.
        self.server_to_slots = {}

    def request_hash(self, request_id):
        return (request_id**2 + 2*request_id + 17) % self.num_slots

    def virtual_server_hash(self, server_id, replica_id):
        i, j = server_id, replica_id
        return (i**2 + j**2 + 2*j + 25) % self.num_slots

    def _find_empty_slot(self, preferred_slot):
        """
        Starting at preferred_slot, do linear probing:
        check preferred_slot, preferred_slot+1, preferred_slot+2, ...
        (wrapping around past 511 back to 0) until an empty slot is found.
        """
        for offset in range(self.num_slots):
            candidate = (preferred_slot + offset) % self.num_slots
            if self.slots[candidate] is None:
                return candidate
        raise Exception("No empty slots available - hash map is full")

    def add_server(self, server_id):
        """
        Places K virtual copies of this server onto the circle.
        Uses linear probing if a preferred slot is already taken.
        """
        placed_slots = []
        for replica_id in range(self.num_virtual_servers):
            preferred_slot = self.virtual_server_hash(server_id, replica_id)
            actual_slot = self._find_empty_slot(preferred_slot)
            self.slots[actual_slot] = server_id
            placed_slots.append(actual_slot)
        
        self.server_to_slots[server_id] = placed_slots

    def remove_server(self, server_id):
        """
        Removes all virtual copies of this server from the circle.
        """
        if server_id not in self.server_to_slots:
            return  # server wasn't in the map, nothing to do
        
        for slot in self.server_to_slots[server_id]:
            self.slots[slot] = None
        
        del self.server_to_slots[server_id]

    def get_server(self, request_id):
        """
        Given a request ID, find which server should handle it:
        hash the request, then walk clockwise until a server is found.
        """
        preferred_slot = self.request_hash(request_id)
        for offset in range(self.num_slots):
            candidate = (preferred_slot + offset) % self.num_slots
            if self.slots[candidate] is not None:
                return self.slots[candidate]
        return None  # no servers in the map at all


if __name__ == "__main__":
    ch = ConsistentHashMap()
    ch.add_server(1)
    ch.add_server(2)
    ch.add_server(3)
    print("Request 15 routed to server:", ch.get_server(15))