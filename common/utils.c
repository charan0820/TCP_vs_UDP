#define _POSIX_C_SOURCE 200809L

#include "utils.h"

#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

uint64_t utils_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int utils_create_tcp_socket(void) {
    return socket(AF_INET, SOCK_STREAM, 0);
}

int utils_create_udp_socket(void) {
    return socket(AF_INET, SOCK_DGRAM, 0);
}

int utils_set_reuseaddr(int sockfd) {
    int opt = 1;
    return setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
}

int utils_bind(int sockfd, const char *address, uint16_t port) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (address == NULL || strcmp(address, "0.0.0.0") == 0) {
        addr.sin_addr.s_addr = INADDR_ANY;
    } else if (inet_pton(AF_INET, address, &addr.sin_addr) != 1) {
        return -1;
    }

    return bind(sockfd, (struct sockaddr *)&addr, sizeof(addr));
}

int utils_connect(int sockfd, const char *address, uint16_t port) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (inet_pton(AF_INET, address, &addr.sin_addr) != 1) {
        return -1;
    }

    return connect(sockfd, (struct sockaddr *)&addr, sizeof(addr));
}

ssize_t utils_write_full(int sockfd, const void *buf, size_t len) {
    size_t total = 0;
    const uint8_t *p = (const uint8_t *)buf;

    while (total < len) {
        ssize_t n = write(sockfd, p + total, len - total);
        if (n < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (n == 0) break;
        total += (size_t)n;
    }
    return (ssize_t)total;
}

ssize_t utils_read_full(int sockfd, void *buf, size_t len) {
    size_t total = 0;
    uint8_t *p = (uint8_t *)buf;

    while (total < len) {
        ssize_t n = read(sockfd, p + total, len - total);
        if (n < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (n == 0) break; /* peer closed the connection */
        total += (size_t)n;
    }
    return (ssize_t)total;
}

void utils_log(const char *fmt, ...) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    struct tm tm_info;
    localtime_r(&ts.tv_sec, &tm_info);

    char timebuf[16];
    strftime(timebuf, sizeof(timebuf), "%H:%M:%S", &tm_info);
    fprintf(stderr, "[%s] ", timebuf);

    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);

    fprintf(stderr, "\n");
}
