# CannelloniPy
Python version of the [Cannelloni library](https://github.com/mguentner/cannelloni)

For now implemented only on the receiver side.

## General logic of the library
![Cannelloni library logic](/img/cannelloni.png)

## Installation
Simply copy and paste the `cannellonipy.py` file into your project.

## Usage
```python
# Import the library
from cannellonipy import run_cannelloni, CannelloniHandle

# Create a cannellonipy handle
cannellonipy_handle = CannelloniHandle()

# Run the library
run_cannellonipy(cannellonipy_handle, "0.0.0.0", 1234)

# Get the received data
received_frames = handle.get_received_can_frames()
for frame in received_frames:
    print("Received CAN frame -> CAN ID:", frame.can_id, ", Length:", frame.len, ", Data:", frame.data[:frame.len].hex())

# After processing, clear the received frames from the buffer
handle.clear_received_can_frames()
```
An example of usage can be found in the `usageTest.py` file.

## TODO
- :white_square_button: Implement CAN transmit
- :white_square_button: Implement CAN receive
- :white_square_button: Implement tests
