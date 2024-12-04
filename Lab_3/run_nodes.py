import threading
import time
from raft_node import RaftNode

# Define maximum runtime for the simulation (in seconds)
MAX_RUNTIME = 30  # Simulation will run for 30 seconds

def main():
    total_nodes = 5
    nodes = [RaftNode(node_id, total_nodes) for node_id in range(total_nodes)]

    threads = []
    for node in nodes:
        thread = threading.Thread(target=node.run)
        thread.start()
        threads.append(thread)

    try:
        start_time = time.time()
        while time.time() - start_time < MAX_RUNTIME:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping nodes due to keyboard interrupt...")
    finally:
        print("Stopping nodes...")
        for node in nodes:
            node.stop()
        for thread in threads:
            thread.join()
        print("Simulation stopped.")

if __name__ == "__main__":
    main()