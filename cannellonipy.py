import struct
import socket

# Constants
CANNELLONI_FRAME_VERSION = 2
CNL_DATA = 1
CANFD_FRAME = 0x80
CANNELLONI_DATA_PACKET_BASE_SIZE = 5
CANNELLONI_FRAME_BASE_SIZE = 5

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

    def put(self):
        if (self.tail + 1) % self.count == self.head:
            return None
        frame = self.frames[self.tail]
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
    def __init__(self, can_tx_fn=None, can_rx_fn=None, can_buf_size=64, port=12345, remote_port=12345):
        self.sequence_number = 0
        self.udp_rx_count = 0
        self.Init = {
            "port": port,
            "addr": "0.0.0.0",
            "remote_port": remote_port,
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

    def handle_cannelloni_frame(handle, data, addr):
        if len(data) < CANNELLONI_DATA_PACKET_BASE_SIZE:
            return

        version, op_code, seq_no, count = struct.unpack('!BBBB', data[:CANNELLONI_DATA_PACKET_BASE_SIZE])
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

    def receive_can_frames(handle):
        if not handle.Init["can_rx_fn"]:
            return
        handle.Init["can_rx_fn"](handle)

    def run_cannelloni(handle):
        transmit_can_frames(handle)
        receive_can_frames(handle)
        while transmit_udp_frame(handle):
            pass

    def get_can_rx_frame(handle):
        return handle.rx_queue.put()

    def canfd_len(frame):
        return frame.len & ~CANFD_FRAME

    def transmit_udp_frame(handle):
        frame = handle.tx_queue.peek()
        if frame is None:
            return False

        data = bytearray(1200)
        view = memoryview(data)
        pos = CANNELLONI_DATA_PACKET_BASE_SIZE

        while frame and pos + CANNELLONI_FRAME_BASE_SIZE + frame.len < len(data):
            frame = handle.tx_queue.take()

            view[pos:pos + 4] = struct.pack('!I', frame.can_id)
            pos += 4
            view[pos] = frame.len
            pos += 1
            view[pos:pos + frame.len] = frame.data[:frame.len]
            pos += frame.len

            frame = handle.tx_queue.peek()

        view[:CANNELLONI_DATA_PACKET_BASE_SIZE] = struct.pack('!BBBB', CANNELLONI_FRAME_VERSION, CNL_DATA, handle.sequence_number, pos - CANNELLONI_DATA_PACKET_BASE_SIZE)
        handle["udp_pcb"].sendto(data[:pos], (handle.Init["addr"], handle.Init["remote_port"]))
        handle["sequence_number"] += 1

        return frame is not None

    def transmit_can_frames(handle):
        if not handle.Init["can_tx_fn"]:
            return
        frame = handle.tx_queue.peek()
        while frame and handle.Init["can_tx_fn"](handle, frame):
            handle.tx_queue.take()
            frame = handle.tx_queue.peek()
