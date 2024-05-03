import struct
import socket
import threading
import time

# ---------------------------- Constants ----------------------------
CANNELLONI_FRAME_VERSION = 2
CNL_DATA = 1
CANFD_FRAME = 0x80
CANNELLONI_DATA_PACKET_BASE_SIZE = 5
CANNELLONI_FRAME_BASE_SIZE = 5
PORT = 1234
REMOTE_PORT = 1234
REMOTE_IP = "0.0.0.0"

# ---------------------------- Utils ----------------------------
class CanfdFrame:
    def __init__(self):
        self.can_id = 0
        self.len = 0
        self.flags = 0
        self.data = bytearray(8)  # Assuming maximum payload size of 8 bytes

class FramesQueue:
    def __init__(self, count):
        self.head = 0
        self.tail = 0
        self.count = count
        self.frames = [CanfdFrame() for _ in range(count)]

    def put(self, frame): 
        if (self.tail + 1) % self.count == self.head:
            return None
        self.frames[self.tail] = frame
        self.tail = (self.tail + 1) % self.count
        return frame

    def take(self):
        if self.head == self.tail:
            return None
        frame = self.frames[self.head]
        self.head = (self.head + 1) % self.count
        return frame

    def peek(self):
        if self.head == self.tail:
            return None
        return self.frames[self.head]

class CannelloniHandle:
    def __init__(self, can_tx_fn=None, can_rx_fn=None, can_buf_size=64):
        self.sequence_number = 0
        self.udp_rx_count = 0
        self.Init = {
            #"port": port,
            "addr": REMOTE_IP,
            "remote_port": REMOTE_PORT,
            "can_buf_size": can_buf_size,
            "can_tx_buf": [CanfdFrame() for _ in range(can_buf_size)],
            "can_rx_buf": [CanfdFrame() for _ in range(can_buf_size)],
            "can_tx_fn": can_tx_fn,
            "can_rx_fn": can_rx_fn,
            "user_data": None
        }
        self.tx_queue = FramesQueue(can_buf_size)
        self.rx_queue = FramesQueue(can_buf_size)
        self.udp_pcb = None
        self.can_pcb = None

    def handle_cannelloni_frame(handle, data, addr):
        if len(data) < CANNELLONI_DATA_PACKET_BASE_SIZE:
            return

        try:
            version, op_code, seq_no, count = struct.unpack('!BBBB', data[:CANNELLONI_DATA_PACKET_BASE_SIZE])
        except struct.error:
            return
            
        if version != CANNELLONI_FRAME_VERSION or op_code != CNL_DATA:
            return

        pos = CANNELLONI_DATA_PACKET_BASE_SIZE
        raw_data = memoryview(data)
        handle["udp_rx_count"] += 1

        for _ in range(count):
            if pos + CANNELLONI_FRAME_BASE_SIZE > len(data):
                # Received incomplete packet
                break

            can_id, len_and_flags = struct.unpack('!IB', raw_data[pos:pos+5])
            pos += 5

            len_ = len_and_flags & ~CANFD_FRAME
            flags = len_and_flags & CANFD_FRAME

            if (can_id & CAN_RTR_FLAG) == 0 and pos + len_ > len(data):
                # Received incomplete packet / can header corrupt!
                break

            frame = handle.rx_queue.put()
            if frame is None:
                # Allocation error
                break

            frame.can_id = can_id
            frame.len = len_
            frame.flags = flags

            if (can_id & CAN_RTR_FLAG) == 0:
                frame.data[:len_] = raw_data[pos:pos + len_]
                pos += len_

            # Print the received frame data
            print("Received CAN frame -> CAN ID: ", frame.can_id, ",Length: ", frame.len, ",Data: ", frame.data[:frame.len].hex(), ",from: ", addr)

# ---------------------------- Execution ----------------------------
def run_cannelloni(handle):
    print("Running Cannelloni...")
    open_udp_socket(handle)
    # open_can_socket(handle) TODO
    handle.can_pcb = True # Mocking the opening of the CAN socket
    if not handle.udp_pcb or not handle.can_pcb:
        print("Failed to open sockets")
        return

    # Start all the service threads 
    receive_can_frames_thread = threading.Thread(target=receive_can_frames, args=(handle,), daemon=True) 
    receive_can_frames_thread.start()
    transmit_can_frames_thread = threading.Thread(target=transmit_can_frames, args=(handle,), daemon=True) 
    transmit_can_frames_thread.start()
    receive_udp_packets_thread = threading.Thread(target=receive_udp_packets, args=(handle,), daemon=True)
    receive_udp_packets_thread.start()
    transmit_udp_packets_thread = threading.Thread(target=transmit_udp_packets, args=(handle,), daemon=True)
    transmit_udp_packets_thread.start()

def open_udp_socket(handle):
    # Create a UDP socket (send/receive)
    try:
        handle.udp_pcb = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Check with cmd:  sudo tcpdump -i any udp port 1234 -X
        handle.udp_pcb.bind((REMOTE_IP, REMOTE_PORT))
        if not handle.udp_pcb:
            print("Failed to create UDP socket")
            return
        else:
            print("UDP socket created successfully on port 1234")
    except Exception as e:
        print("Failed to create UDP socket: ", e)
        return

def open_can_socket(handle):
    try:
        # Create a CAN socket (send/receive)
        # TODO
        if not handle.can_pcb:
            print("Failed to create CAN socket")
            return
        else:
            print("CAN socket created successfully on interface can0")
    except Exception as e:
        print("Failed to create CAN socket: ", e)
        return

def transmit_udp_packets(handle):
    try:
        while True:
            frame = handle.tx_queue.take()
            if frame is not None:
                #print("Transmitting CAN frame: ", frame.data[:frame.len].hex(), "to", handle.Init["addr"], "on port", handle.Init["remote_port"], "with sequence number", handle.sequence_number)
                data = bytearray()
                data.extend(struct.pack('!BBBB', CANNELLONI_FRAME_VERSION, CNL_DATA, handle.sequence_number, 1))
                data.extend(struct.pack('!IB', frame.can_id, frame.len | frame.flags))
                data.extend(frame.data[:frame.len])
                print("Transmitting UDP packet with data:", data)
                handle.udp_pcb.sendto(data, (REMOTE_IP, REMOTE_PORT))
    except Exception as e:
        print("Error while transmitting UDP packets: ", e)
        return

def receive_udp_packets(handle):
    try:
        while True:
            data, addr = handle.udp_pcb.recvfrom(1024)
            if data:
                handle.handle_cannelloni_frame(data, addr)
                print("Received UDP packet from", addr, "with data:", data.hex())
    except Exception as e:
        print("Error while receiving UDP packets: ", e)
        return

def receive_can_frames(handle):
    # TODO: Implement this function
    # This function should receive CAN frames and put them in the tx_queue
    pass

def transmit_can_frames(handle):
    # TODO: Implement this function
    # This function should transmit CAN frames from the rx_queue
    pass
