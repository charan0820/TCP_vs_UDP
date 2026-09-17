#include "protocol.h"
#include <string.h>

size_t packet_header_size(void) {
    return sizeof(packet_header_t);
}

size_t packet_total_size(uint32_t payload_size) {
    return sizeof(packet_header_t) + payload_size;
}

void packet_init(app_packet_t *pkt, const char *experiment_id,
                  uint64_t seq, uint32_t payload_size) {
    memset(pkt, 0, sizeof(*pkt));
    pkt->header.magic = PROTOCOL_MAGIC;
    strncpy(pkt->header.experiment_id, experiment_id, EXPERIMENT_ID_LEN - 1);
    pkt->header.sequence_number = seq;
    pkt->header.timestamp_ns = 0; /* caller sets the real send time */

    if (payload_size > MAX_PAYLOAD_SIZE) {
        payload_size = MAX_PAYLOAD_SIZE;
    }
    pkt->header.payload_size = payload_size;
}

int packet_validate(const app_packet_t *pkt) {
    if (pkt->header.magic != PROTOCOL_MAGIC) {
        return 0;
    }
    if (pkt->header.payload_size > MAX_PAYLOAD_SIZE) {
        return 0;
    }
    return 1;
}
