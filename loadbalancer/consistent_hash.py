import os


class ConsistentHashMap:
    def __init__(self, num_slots=512, num_virtual_servers=9, hash_variant=None):
        self.num_slots = num_slots
        self.num_virtual_servers = num_virtual_servers
        
        # hash_variant can be "original" or "improved".
        # If not explicitly passed in, check environment variable, default to "original".
        self.hash_variant = hash_variant or os.environ.get("HASH_VARIANT", "original")
        
        self.slots = [None] * num_slots
        self.server_to_slots = {}

    def request_hash(self, request_id):
        if self.hash_variant == "improved":
            return (request_id * 2654435761) % self.num_slots
        else:
            return (request_id**2 + 2*request_id + 17) % self.num_slots

    def virtual_server_hash(self, server_id, replica_id):
        i, j = server_id, replica_id
        if self.hash_variant == "improved":
            return ((i * 2654435761) + (j * 40503) + 17) % self.num_slots
        else:
            return (i**2 + j**2 + 2*j + 25) % self.num_slots

    def _find_empty_slot(self, preferred_slot):
        for offset in range(self.num_slots):
            candidate = (preferred_slot + offset) % self.num_slots
            if self.slots[candidate] is None:
                return candidate
        raise Exception("No empty slots available - hash map is full")

    def add_server(self, server_id):
        placed_slots = []
        for replica_id in range(self.num_virtual_servers):
            preferred_slot = self.virtual_server_hash(server_id, replica_id)
            actual_slot = self._find_empty_slot(preferred_slot)
            self.slots[actual_slot] = server_id
            placed_slots.append(actual_slot)
        
        self.server_to_slots[server_id] = placed_slots

    def remove_server(self, server_id):
        if server_id not in self.server_to_slots:
            return
        
        for slot in self.server_to_slots[server_id]:
            self.slots[slot] = None
        
        del self.server_to_slots[server_id]

    def get_server(self, request_id):
        preferred_slot = self.request_hash(request_id)
        for offset in range(self.num_slots):
            candidate = (preferred_slot + offset) % self.num_slots
            if self.slots[candidate] is not None:
                return self.slots[candidate]
        return None


if __name__ == "__main__":
    ch = ConsistentHashMap()
    ch.add_server(1)
    ch.add_server(2)
    ch.add_server(3)
    print("Request 15 routed to server:", ch.get_server(15))