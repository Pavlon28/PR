import socket
import threading
import time
import random

# Constants
FOLLOWER = "Follower"
CANDIDATE = "Candidate"
LEADER = "Leader"
HEARTBEAT_INTERVAL = 2  # Seconds
ELECTION_TIMEOUT_RANGE = (5, 10)  # Randomized range for election timeout in seconds
PORT_BASE = 5000  # Base port for nodes

class RaftNode:
    def __init__(self, node_id, total_nodes):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.state = FOLLOWER
        self.term = 0
        self.votes = 0
        self.leader_id = None
        self.last_heartbeat = time.time()
        self.running = True
        self.election_timeout = random.uniform(*ELECTION_TIMEOUT_RANGE)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("localhost", PORT_BASE + node_id))
        self.lock = threading.Lock()  # Protect shared resources
        self.threads = []

    def log(self, message):
        print(f"[Node {self.node_id} - {self.state}] {message}")

    def send_message(self, target_id, message):
        with self.lock:  # Ensure safe access to the socket
            if self.running:  # Check if the node is running before sending
                self.sock.sendto(message.encode(), ("localhost", PORT_BASE + target_id))

    def broadcast_message(self, message):
        for target_id in range(self.total_nodes):
            if target_id != self.node_id:
                self.send_message(target_id, message)

    def receive_messages(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                if not self.running:  # Stop processing if the node is shutting down
                    break
                message = data.decode()
                self.handle_message(message)
            except OSError:
                break  # Exit the loop if the socket is closed

    def handle_message(self, message):
        parts = message.split("|")
        if parts[0] == "HEARTBEAT":
            self.leader_id = int(parts[1])
            self.last_heartbeat = time.time()
            self.log(f"Received heartbeat from Leader {self.leader_id}")
        elif parts[0] == "VOTE_REQUEST":
            candidate_id = int(parts[1])
            if self.state == FOLLOWER and self.term <= int(parts[2]):
                self.term = int(parts[2])
                self.send_message(candidate_id, f"VOTE_GRANTED|{self.node_id}")
                self.log(f"Voted for Candidate {candidate_id}")
        elif parts[0] == "VOTE_GRANTED":
            self.votes += 1
            self.log(f"Received vote from Node {parts[1]}")
            if self.votes > self.total_nodes // 2:
                self.become_leader()

    def become_leader(self):
        self.state = LEADER
        self.log("Became Leader")
        self.broadcast_message(f"HEARTBEAT|{self.node_id}")

    def start_election(self):
        self.state = CANDIDATE
        self.term += 1
        self.votes = 1  # Vote for itself
        self.broadcast_message(f"VOTE_REQUEST|{self.node_id}|{self.term}")
        self.log("Started election")

    def run(self):
        receiver_thread = threading.Thread(target=self.receive_messages)
        receiver_thread.start()
        self.threads.append(receiver_thread)

        while self.running:
            time.sleep(1)
            if self.state == LEADER:
                self.broadcast_message(f"HEARTBEAT|{self.node_id}")
            elif self.state == FOLLOWER and time.time() - self.last_heartbeat > self.election_timeout:
                self.start_election()

    def stop(self):
        self.running = False
        with self.lock:  # Safely close the socket
            self.sock.close()
        for thread in self.threads:
            thread.join()