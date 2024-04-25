#include "cannelloni.h"

#define CNL_BUF_SIZE 16

cannelloni_handle_t cannelloni_handle;
struct canfd_frame tx_buf[CNL_BUF_SIZE];
struct canfd_frame rx_buf[CNL_BUF_SIZE];

/* to be set in a timer routine */
volatile uint8_t tcp_timeout = 0;
volatile uint8_t arp_timeout = 0;

typedef struct {
    uint32_t id;            // CAN message ID
    uint8_t len;            // Length of the data in bytes
    uint8_t data[8];        // Data bytes of the CAN message
} CanMessage;

// void my_can_transmit(cannelloni_handle_t *const handle, struct canfd_frame *frame) 

void open_stream(cannelloni_handle_t *const handle) {
  // TO DO
}

// void my_can_receive(cannelloni_handle_t *const handle) {
//   if (is_can_frame_pending()) {
//     CanMessage msg;
//     read_can_frame_from_controller(&msg);
// 		struct canfd_frame *frame = get_can_rx_frame(&handle);
// 		if (frame) {
// 			frame->can_id = msg.id;
// 			frame->len = msg.len;
// 			frame->data[0] = msg.data[0] >> 24 & 0x000000ff;
// 			frame->data[1] = msg.data[0] >> 16 & 0x000000ff;
// 			frame->data[2] = msg.data[0] >> 8  & 0x000000ff;
// 			frame->data[3] = msg.data[0]       & 0x000000ff;
// 			frame->data[4] = msg.data[1] >> 24 & 0x000000ff;
// 			frame->data[5] = msg.data[1] >> 16 & 0x000000ff;
// 			frame->data[6] = msg.data[1] >> 8  & 0x000000ff;
// 			frame->data[7] = msg.data[1]       & 0x000000ff;
// 		}
// 	}
// }

void init(void) {
    IP4_ADDR(&cannelloni_handle.Init.addr, 10, 10, 10, 10);
    cannelloni_handle.Init.can_buf_size = CNL_BUF_SIZE;
    cannelloni_handle.Init.can_rx_buf = rx_buf;
    cannelloni_handle.Init.can_rx_fn = my_can_receive;
    cannelloni_handle.Init.can_tx_buf = tx_buf;
    cannelloni_handle.Init.can_tx_fn = my_can_transmit;
    cannelloni_handle.Init.port = 20000;
    cannelloni_handle.Init.remote_port = 20000;

    // TO DO
    init_can();
    init_ethernet();
    init_lwip();
    init_cannelloni(&cannelloni_handle);
}

void _main(void) {
    init_system();
    while(1) {
        if (tcp_timeout) {
        tcp_tmr();
        tcp_timeout = 0;
        }
        if (arp_timeout) {
        etharp_tmr();
        ip_reass_tmr();
        }
        run_cannelloni(&cannelloni_handle);
    }
}

