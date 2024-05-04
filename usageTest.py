import time
import threading
import socket
from cannellonipy import run_cannellonipy, CanfdFrame, CannelloniHandle

# Initialize CannelloniHandle
handle = CannelloniHandle()

# Run cannelloni
run_cannellonipy(handle, "0.0.0.0", 1234)

# Send a frame in the vcan0 interface
example_data = bytearray(b'Hello, World!')
example_frame = CanfdFrame()
example_frame.can_id = 123  # Example CAN ID
example_frame.len = len(example_data)
example_frame.data[:example_frame.len] = example_data

# Second CAN frame:
example_data_2 = bytearray(b'Second frame!')
example_frame_2 = CanfdFrame()
example_frame_2.can_id = 123  # Example CAN ID
example_frame_2.len = len(example_data_2)
example_frame_2.data[:example_frame_2.len] = example_data_2

# Mock the receiving of can messages from the vcan0 interface
while True:
    print("Creating CAN frame: ", example_frame.data[:example_frame.len].hex(), "to", handle.Init["addr"], "on port", handle.Init["remote_port"], "with sequence number", handle.sequence_number)
    handle.tx_queue.put(example_frame)
    time.sleep(2)
    # print("Creating CAN frame: ", example_frame_2.data[:example_frame_2.len].hex(), "to", handle.Init["addr"], "on port", handle.Init["remote_port"], "with sequence number", handle.sequence_number)
    # handle.tx_queue.put(example_frame_2)
    # time.sleep(2)

    # Get received frames
    received_frames = handle.get_received_can_frames()
    for frame in received_frames:
        print("Received CAN frame -> CAN ID:", frame.can_id, ", Length:", frame.len, ", Data:", frame.data[:frame.len].hex())

    # After processing, clear the received frames buffer
    handle.clear_received_can_frames()
