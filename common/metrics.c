#include "metrics.h"
#include <stdio.h>

static FILE *g_log_file = NULL;

static const char *event_type_str(metric_event_type_t t) {
    switch (t) {
        case EVENT_SEND:     return "SEND";
        case EVENT_RECV:     return "RECV";
        case EVENT_ACK_SEND: return "ACK_SEND";
        case EVENT_ACK_RECV: return "ACK_RECV";
        default:              return "UNKNOWN";
    }
}

int metrics_log_open(const char *filepath) {
    g_log_file = fopen(filepath, "w");
    if (g_log_file == NULL) {
        return -1;
    }
    fprintf(g_log_file,
            "event_type,experiment_id,protocol,sequence_number,timestamp_ns,payload_size\n");
    return 0;
}

void metrics_log_event(const metric_event_t *evt) {
    if (g_log_file == NULL) return;

    fprintf(g_log_file, "%s,%s,%s,%llu,%llu,%u\n",
            event_type_str(evt->event_type),
            evt->experiment_id,
            evt->protocol,
            (unsigned long long)evt->sequence_number,
            (unsigned long long)evt->timestamp_ns,
            evt->payload_size);
    fflush(g_log_file); /* flush per-event: acceptable for prototype scale */
}

void metrics_log_close(void) {
    if (g_log_file != NULL) {
        fclose(g_log_file);
        g_log_file = NULL;
    }
}
