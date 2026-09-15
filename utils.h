#ifndef UTILS_H
#define UTILS_H

#include <stdint.h>
#include <stddef.h>
#include <sys/types.h>

/* ============================================================
 * Shared low-level helpers used by both the TCP and UDP client
 * and server implementations, so socket setup, timing, and
 * logging behave identically across protocols. Implemented in
 * common/utils.c (Member 1).
 * ============================================================ */

/* Monotonic timestamp in nanoseconds (CLOCK_MONOTONIC). Used to
 * stamp every packet and to compute latency/jitter. */
uint64_t utils_now_ns(void);

/* Socket setup helpers. */
int utils_create_tcp_socket(void);
int utils_create_udp_socket(void);
int utils_set_reuseaddr(int sockfd);
int utils_bind(int sockfd, const char *address, uint16_t port);
int utils_connect(int sockfd, const char *address, uint16_t port);

/* TCP is a byte stream: these wrappers guarantee that exactly
 * `len` bytes are written/read (looping over partial
 * send/recv), so packet_header_t + payload framing on top of
 * protocol.h is reliable. */
ssize_t utils_write_full(int sockfd, const void *buf, size_t len);
ssize_t utils_read_full(int sockfd, void *buf, size_t len);

/* Minimal timestamped logger, prints to stderr:
 *   [utils_log] printf-style. */
void utils_log(const char *fmt, ...);

#endif /* UTILS_H */
