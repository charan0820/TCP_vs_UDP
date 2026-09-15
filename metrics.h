#ifndef METRICS_H
#define METRICS_H

#include <stdint.h>

/* ============================================================
 * Raw per-packet event log format.
 *
 * The TCP/UDP clients and servers (Member 1) each write one line
 * per packet-level event to a plaintext log file during a run.
 * metrics/collector.py and metrics/parser.py (Member 2) read this
 * log and reduce it into the single aggregated CSV row per
 * experiment described below, which analysis/ and visualization/
 * (Member 3) consume. This is the Day-1 contract between all
 * three members -- do not change field names/order without
 * updating this file and telling the other two members.
 *
 * Log line format (one event per line, comma separated):
 *   event_type,experiment_id,protocol,sequence_number,timestamp_ns,payload_size
 *
 * event_type : SEND | RECV | ACK_SEND | ACK_RECV
 * protocol   : TCP | UDP
 * ============================================================ */

typedef enum {
    EVENT_SEND = 0,      /* client sent a data packet */
    EVENT_RECV = 1,      /* server received a data packet */
    EVENT_ACK_SEND = 2,  /* server sent an ack/response */
    EVENT_ACK_RECV = 3   /* client received an ack/response */
} metric_event_type_t;

typedef struct {
    metric_event_type_t event_type;
    char     experiment_id[16];
    char     protocol[4];       /* "TCP" or "UDP" */
    uint64_t sequence_number;
    uint64_t timestamp_ns;
    uint32_t payload_size;
} metric_event_t;

/* --- Logging API, implemented in common/metrics.c (Member 1) --- */

/* Open (create/truncate) the raw event log file for this run.
 * Returns 0 on success, -1 on failure. */
int metrics_log_open(const char *filepath);

/* Append one event line to the currently open log. */
void metrics_log_event(const metric_event_t *evt);

/* Flush and close the currently open log. */
void metrics_log_close(void);

/* ------------------------------------------------------------
 * Aggregated per-experiment CSV schema (Member 2 -> Member 3
 * handoff). Every completed experiment run must produce exactly
 * one row of this shape in data/processed/. Column order matches
 * the project's canonical schema so downstream code can rely on
 * position as well as name.
 *
 *   experiment_id
 *   protocol
 *   packet_size
 *   packet_count
 *   duration
 *   bytes_sent
 *   bytes_received
 *   throughput_mbps
 *   avg_latency_ms
 *   min_latency_ms
 *   max_latency_ms
 *   jitter_ms
 *   packet_loss_percent
 *   retransmissions
 *   timestamp
 *
 * Example row:
 *   EXP001,TCP,1024,10000,10,10240000,10240000,8.2,2.1,1.2,8.7,0.4,0,2026-09-20
 * ------------------------------------------------------------ */

#endif /* METRICS_H */
