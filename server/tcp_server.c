/*
 * tcp_server.c
 * Member 1 -- Networking Core (Day 2)
 *
 * Accepts TCP connections, reads app-level packets framed with
 * packet_header_t + payload (see common/protocol.h), logs a RECV
 * event per packet, and echoes back a zero-payload ack carrying
 * the same sequence number so the client can measure round-trip
 * latency. Every packet event is written to a CSV log via
 * common/metrics.h for Member 2's pipeline to pick up.
 *
 * Usage:
 *   tcp_server [port] [metrics_log_path]
 *   tcp_server 5001 data/raw/tcp_server_events.csv
 */

#include "../common/protocol.h"
#include "../common/metrics.h"
#include "../common/utils.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

static volatile sig_atomic_t g_running = 1;

static void handle_sigint(int sig) {
    (void)sig;
    g_running = 0;
}

static void log_event(metric_event_type_t type, const char *experiment_id,
                       uint64_t seq, uint64_t ts_ns, uint32_t payload_size) {
    metric_event_t evt;
    memset(&evt, 0, sizeof(evt));
    evt.event_type = type;
    strncpy(evt.experiment_id, experiment_id, sizeof(evt.experiment_id) - 1);
    memcpy(evt.protocol, "TCP", 3);
    evt.sequence_number = seq;
    evt.timestamp_ns = ts_ns;
    evt.payload_size = payload_size;
    metrics_log_event(&evt);
}

static void handle_client(int client_fd) {
    app_packet_t pkt;

    while (g_running) {
        ssize_t hn = utils_read_full(client_fd, &pkt.header, packet_header_size());
        if (hn <= 0) {
            break; /* client closed the connection, or an error occurred */
        }
        if ((size_t)hn < packet_header_size()) {
            utils_log("tcp_server: short header read (%zd/%zu bytes), closing connection",
                       hn, packet_header_size());
            break;
        }

        if (!packet_validate(&pkt)) {
            utils_log("tcp_server: invalid packet header (bad magic), closing connection");
            break;
        }

        if (pkt.header.payload_size > 0) {
            ssize_t pn = utils_read_full(client_fd, pkt.payload, pkt.header.payload_size);
            if (pn < 0 || (uint32_t)pn < pkt.header.payload_size) {
                utils_log("tcp_server: short payload read, closing connection");
                break;
            }
        }

        uint64_t recv_ts = utils_now_ns();
        log_event(EVENT_RECV, pkt.header.experiment_id,
                   pkt.header.sequence_number, recv_ts, pkt.header.payload_size);

        /* Zero-payload ack: enough for the client to compute
         * round-trip latency without doubling network load. */
        app_packet_t ack;
        packet_init(&ack, pkt.header.experiment_id, pkt.header.sequence_number, 0);
        ack.header.timestamp_ns = utils_now_ns();

        ssize_t wn = utils_write_full(client_fd, &ack.header, packet_header_size());
        if (wn < 0 || (size_t)wn < packet_header_size()) {
            utils_log("tcp_server: failed to send ack, closing connection");
            break;
        }

        log_event(EVENT_ACK_SEND, ack.header.experiment_id,
                   ack.header.sequence_number, ack.header.timestamp_ns, 0);
    }

    close(client_fd);
}

int main(int argc, char *argv[]) {
    uint16_t port = 5001;
    const char *log_path = "data/raw/tcp_server_events.csv";
    const char *address = "0.0.0.0";

    if (argc > 1) port = (uint16_t)atoi(argv[1]);
    if (argc > 2) log_path = argv[2];

    signal(SIGINT, handle_sigint);

    if (metrics_log_open(log_path) != 0) {
        utils_log("tcp_server: failed to open metrics log at %s", log_path);
        return 1;
    }

    int listen_fd = utils_create_tcp_socket();
    if (listen_fd < 0) {
        utils_log("tcp_server: socket() failed");
        return 1;
    }
    utils_set_reuseaddr(listen_fd);

    if (utils_bind(listen_fd, address, port) != 0) {
        utils_log("tcp_server: bind() failed on %s:%u", address, port);
        close(listen_fd);
        return 1;
    }

    if (listen(listen_fd, 16) != 0) {
        utils_log("tcp_server: listen() failed");
        close(listen_fd);
        return 1;
    }

    utils_log("tcp_server: listening on %s:%u (log: %s)", address, port, log_path);

    while (g_running) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);
        int client_fd = accept(listen_fd, (struct sockaddr *)&client_addr, &addr_len);
        if (client_fd < 0) {
            if (!g_running) break;
            continue;
        }

        /* Disable Nagle's algorithm: experiment packets are small
         * and latency-sensitive, so we don't want them batched. */
        int flag = 1;
        setsockopt(client_fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));

        char ip_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, ip_str, sizeof(ip_str));
        utils_log("tcp_server: accepted connection from %s:%u",
                   ip_str, ntohs(client_addr.sin_port));

        handle_client(client_fd);

        utils_log("tcp_server: connection closed");
    }

    close(listen_fd);
    metrics_log_close();
    utils_log("tcp_server: shutting down");
    return 0;
}
