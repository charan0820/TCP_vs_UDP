#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include <stddef.h>

/* ============================================================
 * Application-level packet/message format shared by the TCP and
 * UDP clients and servers.
 *
 * TCP is a byte-stream protocol, so this header is prefixed to
 * every logical message before it is written to the socket, and
 * the receiver must read it back out explicitly (see
 * utils_write_full/utils_read_full in utils.h).
 *
 * UDP preserves datagram boundaries, so header + payload forms
 * exactly one datagram per sendto()/recvfrom().
 *
 * The logical fields are identical for both protocols so that
 * downstream metrics/analysis code does not need to care which
 * transport produced them.
 * ============================================================ */

#define PROTOCOL_MAGIC     0x54554450u   /* "TUDP", sanity check on parse */
#define MAX_PAYLOAD_SIZE   8192          /* covers largest configured packet size */
#define EXPERIMENT_ID_LEN  16            /* e.g. "EXP001" */

#pragma pack(push, 1)

typedef struct {
    uint32_t magic;                          /* PROTOCOL_MAGIC */
    char     experiment_id[EXPERIMENT_ID_LEN];
    uint64_t sequence_number;                /* monotonically increasing per run */
    uint64_t timestamp_ns;                   /* sender's CLOCK_MONOTONIC timestamp, ns */
    uint32_t payload_size;                   /* valid bytes in payload[] */
} packet_header_t;

typedef struct {
    packet_header_t header;
    uint8_t payload[MAX_PAYLOAD_SIZE];
} app_packet_t;

#pragma pack(pop)

/* Control message types, for the small set of non-data exchanges
 * (experiment start/end handshake, acks). Data payload framing
 * itself always uses packet_header_t above. */
typedef enum {
    MSG_DATA = 0,
    MSG_ACK = 1,
    MSG_START_EXPERIMENT = 2,
    MSG_END_EXPERIMENT = 3
} message_type_t;

/* --- Helper API, implemented in common/protocol.c (Member 1) --- */

/* Size in bytes of just the header. */
size_t packet_header_size(void);

/* Size in bytes of header + payload_size bytes of payload
 * (i.e. how many bytes to actually send/recv on the wire). */
size_t packet_total_size(uint32_t payload_size);

/* Fill in header fields and zero the payload region up to payload_size. */
void packet_init(app_packet_t *pkt, const char *experiment_id,
                  uint64_t seq, uint32_t payload_size);

/* Validate magic number and payload_size bounds.
 * Returns 1 if valid, 0 otherwise. */
int packet_validate(const app_packet_t *pkt);

#endif /* PROTOCOL_H */
