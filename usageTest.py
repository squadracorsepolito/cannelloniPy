import time
import threading
import socket
from cannellonipy import run_cannelloni, CanfdFrame, CannelloniHandle

# Initialize CannelloniHandle
handle = CannelloniHandle()

# Run cannelloni
run_cannelloni(handle)

# Send a message in the vcan0 interface
example_packet = bytearray(b'Hello, World!')
example_frame = CanfdFrame()
example_frame.can_id = 123  # Example CAN ID
example_frame.len = len(example_packet)
example_frame.data[:example_frame.len] = example_packet

# Mock the receiving of can messages from the vcan0 interface
while True:
    print("Creating CAN frame: ", example_frame.data[:example_frame.len].hex(), "to", handle.Init["addr"], "on port", handle.Init["remote_port"], "with sequence number", handle.sequence_number)
    handle.tx_queue.put(example_frame)
    time.sleep(2)

