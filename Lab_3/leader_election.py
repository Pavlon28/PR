import socket
import threading
import time
import random

class Node:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.peers = peers
        self.state = "follower"
        self.voted_for = None
        self.leader = None
        self.timeout = random.randint(5, 10)  # Election timeout in seconds
        self.lock = threading.Lock()
        self.simulation_end_time = None

    def send_message(self, target, message):
        """Send a UDP message to a peer."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(message.encode(), target)

    def receive_messages(self):
        """Listen for incoming messages and handle them."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("127.0.0.1", 5000 + self.node_id))
            while time.time() < self.simulation_end_time:
                data, _ = sock.recvfrom(1024)
                message = data.decode()
                self.handle_message(message)

    def handle_message(self, message):
        """Process received messages."""
        with self.lock:
            if message.startswith("heartbeat"):
                self.timeout = random.randint(5, 10)  # Reset timeout
                self.leader = int(message.split()[1])
                print(f"Node {self.node_id} received heartbeat from Leader {self.leader}")
            elif message.startswith("vote_request"):
                candidate_id = int(message.split()[1])
                if self.voted_for is None:
                    self.voted_for = candidate_id
                    self.send_message(("127.0.0.1", 5000 + candidate_id), f"vote_granted {self.node_id}")
                    print(f"Node {self.node_id} voted for {candidate_id}")
            elif message.startswith("vote_granted"):
                print(f"Node {self.node_id} received a vote from Node {message.split()[1]}")

    def start_election(self):
        """Start an election process."""
        with self.lock:
            self.state = "candidate"
            self.voted_for = self.node_id
            votes = 1  # Vote for itself
            for peer in self.peers:
                self.send_message(peer, f"vote_request {self.node_id}")
            start_time = time.time()
            while time.time() - start_time < 2:
                if votes > len(self.peers) // 2:
                    self.state = "leader"
                    self.leader = self.node_id
                    print(f"Node {self.node_id} became the leader!")
                    self.send_heartbeats()
                    return
            self.state = "follower"

    def send_heartbeats(self):
        """Send periodic heartbeats to peers as the leader."""
        while self.state == "leader" and time.time() < self.simulation_end_time:
            for peer in self.peers:
                self.send_message(peer, f"heartbeat {self.node_id}")
            time.sleep(2)

    def run(self, simulation_duration):
        """Run the node, handling timeouts and elections."""
        self.simulation_end_time = time.time() + simulation_duration
        threading.Thread(target=self.receive_messages, daemon=True).start()
        while time.time() < self.simulation_end_time:
            time.sleep(1)
            self.timeout -= 1
            if self.timeout <= 0 and self.state != "leader":
                print(f"Node {self.node_id} starting an election...")
                self.start_election()


if __name__ == "__main__":
    # Configuration
    num_nodes = 5  # Number of nodes in the simulation
    simulation_duration = 30  # Duration of the simulation in seconds

    # Initialize nodes and peers
    nodes = []
    peers = [("127.0.0.1", 5000 + i) for i in range(num_nodes)]
    for i in range(num_nodes):
        node_peers = peers[:i] + peers[i + 1:]
        nodes.append(Node(i, node_peers))

    # Start all nodes
    for node in nodes:
        threading.Thread(target=node.run, args=(simulation_duration,), daemon=True).start()

    # Keep the program running for the simulation duration
    time.sleep(simulation_duration)
    print("Simulation finished.")