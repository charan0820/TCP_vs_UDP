# TCP / UDP measured simulation report

Source: real NS-3 runs. See manifest.json for versions, configuration, seed and source hash.

Goodput uses received payload bytes divided by generation + drain time. Delivery delay is one-way application delay, including buffering and reassembly; it is not RTT.

| Protocol | Condition | Payload B | Rate Mbps | Metric | Mean | Median | Std (population) | P95 across runs | n |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| TCP | clean | 1024 | 5 | throughput_mbps | 0.410 | 0.410 | 0.000 | 0.410 | 2 |
| TCP | clean | 1024 | 5 | avg_latency_ms | 404.807 | 404.807 | 0.000 | 404.807 | 2 |
| TCP | clean | 1024 | 5 | jitter_ms | 4.618 | 4.618 | 0.000 | 4.618 | 2 |
| TCP | clean | 1024 | 5 | packet_loss_percent | 0.000 | 0.000 | 0.000 | 0.000 | 2 |
| TCP | clean | 1024 | 5 | retransmissions | 18.000 | 18.000 | 0.000 | 18.000 | 2 |
| TCP | impaired | 1024 | 5 | throughput_mbps | 0.304 | 0.304 | 0.105 | 0.399 | 2 |
| TCP | impaired | 1024 | 5 | avg_latency_ms | 1972.131 | 1972.131 | 1083.136 | 2946.953 | 2 |
| TCP | impaired | 1024 | 5 | jitter_ms | 22.595 | 22.595 | 11.667 | 33.095 | 2 |
| TCP | impaired | 1024 | 5 | packet_loss_percent | 0.000 | 0.000 | 0.000 | 0.000 | 2 |
| TCP | impaired | 1024 | 5 | retransmissions | 14.500 | 14.500 | 2.500 | 16.750 | 2 |
| UDP | clean | 1024 | 5 | throughput_mbps | 0.190 | 0.190 | 0.000 | 0.190 | 2 |
| UDP | clean | 1024 | 5 | avg_latency_ms | 127.338 | 127.338 | 0.000 | 127.338 | 2 |
| UDP | clean | 1024 | 5 | jitter_ms | 1.296 | 1.296 | 0.000 | 1.296 | 2 |
| UDP | clean | 1024 | 5 | packet_loss_percent | 53.500 | 53.500 | 0.000 | 53.500 | 2 |
| UDP | impaired | 1024 | 5 | throughput_mbps | 0.183 | 0.183 | 0.003 | 0.186 | 2 |
| UDP | impaired | 1024 | 5 | avg_latency_ms | 126.882 | 126.882 | 0.023 | 126.903 | 2 |
| UDP | impaired | 1024 | 5 | jitter_ms | 1.318 | 1.318 | 0.017 | 1.333 | 2 |
| UDP | impaired | 1024 | 5 | packet_loss_percent | 55.250 | 55.250 | 0.750 | 55.925 | 2 |

Per-message p95 delay is stored separately in results.csv. P95 in this table describes the distribution of run summaries.

## Observations

- TCP, clean, 1024 B, 5 Mbps offered: mean goodput 0.410 Mbps; mean 400.0 messages sent and 400.0 delivered. 2/2 runs delivered every complete sent message; 2/2 delivered the full requested count within the observation window.
- TCP, impaired, 1024 B, 5 Mbps offered: mean goodput 0.304 Mbps; mean 297.0 messages sent and 297.0 delivered. 2/2 runs delivered every complete sent message; 1/2 delivered the full requested count within the observation window.
- UDP, clean, 1024 B, 5 Mbps offered: mean goodput 0.190 Mbps; mean 400.0 messages sent and 186.0 delivered. 0/2 runs delivered every complete sent message; 0/2 delivered the full requested count within the observation window.
- UDP, impaired, 1024 B, 5 Mbps offered: mean goodput 0.183 Mbps; mean 400.0 messages sent and 179.0 delivered. 0/2 runs delivered every complete sent message; 0/2 delivered the full requested count within the observation window.

## Interpretation limits

A missing TCP message is undelivered at the finite observation cutoff; it does not establish permanent TCP loss. A run can stop generating before the requested count because of duration or backpressure. Zero deliveries produce missing latency, never zero latency. UDP does not have transport retransmissions. Packet loss settings apply independently to received link packets in both directions, including ACKs. Large UDP messages can fragment. CPU cost is not measured; simulator wall time is not endpoint CPU usage.

Random run numbers differ across repetitions. Multiple protocols and conditions share run numbers for reproducibility, not identical packet loss sequences. Conclusions apply only to the configured topology and workload.