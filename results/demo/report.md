# TCP / UDP measured simulation report

Source: real NS-3 runs. See manifest.json for versions, configuration, seed and source hash.

Goodput uses received payload bytes divided by generation + drain time. Delivery delay is one-way application delay, including buffering and reassembly; it is not RTT.

| Protocol | Condition | Payload B | Rate Mbps | Metric | Mean | Median | Std (population) | P95 across runs | n |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| TCP | clean | 1024 | 20 | throughput_mbps | 5.937 | 5.937 | 0.000 | 5.937 | 3 |
| TCP | clean | 1024 | 20 | avg_latency_ms | 97.085 | 97.085 | 0.000 | 97.085 | 3 |
| TCP | clean | 1024 | 20 | jitter_ms | 0.790 | 0.790 | 0.000 | 0.790 | 3 |
| TCP | clean | 1024 | 20 | packet_loss_percent | 0.000 | 0.000 | 0.000 | 0.000 | 3 |
| TCP | clean | 1024 | 20 | retransmissions | 23.000 | 23.000 | 0.000 | 23.000 | 3 |
| TCP | lossy | 1024 | 20 | throughput_mbps | 1.474 | 1.492 | 0.175 | 1.660 | 3 |
| TCP | lossy | 1024 | 20 | avg_latency_ms | 462.427 | 436.356 | 81.758 | 559.350 | 3 |
| TCP | lossy | 1024 | 20 | jitter_ms | 6.124 | 5.873 | 1.173 | 7.490 | 3 |
| TCP | lossy | 1024 | 20 | packet_loss_percent | 0.000 | 0.000 | 0.000 | 0.000 | 3 |
| TCP | lossy | 1024 | 20 | retransmissions | 18.667 | 18.000 | 0.943 | 19.800 | 3 |
| UDP | clean | 1024 | 20 | throughput_mbps | 5.079 | 5.079 | 0.000 | 5.079 | 3 |
| UDP | clean | 1024 | 20 | avg_latency_ms | 94.887 | 94.887 | 0.000 | 94.887 | 3 |
| UDP | clean | 1024 | 20 | jitter_ms | 0.061 | 0.061 | 0.000 | 0.061 | 3 |
| UDP | clean | 1024 | 20 | packet_loss_percent | 50.400 | 50.400 | 0.000 | 50.400 | 3 |
| UDP | lossy | 1024 | 20 | throughput_mbps | 4.979 | 4.981 | 0.006 | 4.984 | 3 |
| UDP | lossy | 1024 | 20 | avg_latency_ms | 94.879 | 94.879 | 0.007 | 94.886 | 3 |
| UDP | lossy | 1024 | 20 | jitter_ms | 0.062 | 0.062 | 0.000 | 0.062 | 3 |
| UDP | lossy | 1024 | 20 | packet_loss_percent | 51.377 | 51.360 | 0.054 | 51.441 | 3 |

Per-message p95 delay is stored separately in results.csv. P95 in this table describes the distribution of run summaries.

## Observations

- TCP, clean, 1024 B, 20 Mbps offered: mean goodput 5.937 Mbps; mean 5798.0 messages sent and 5798.0 delivered. 3/3 runs delivered every complete sent message; 0/3 delivered the full requested count within the observation window.
- TCP, lossy, 1024 B, 20 Mbps offered: mean goodput 1.474 Mbps; mean 1439.0 messages sent and 1439.0 delivered. 3/3 runs delivered every complete sent message; 0/3 delivered the full requested count within the observation window.
- UDP, clean, 1024 B, 20 Mbps offered: mean goodput 5.079 Mbps; mean 10000.0 messages sent and 4960.0 delivered. 0/3 runs delivered every complete sent message; 0/3 delivered the full requested count within the observation window.
- UDP, lossy, 1024 B, 20 Mbps offered: mean goodput 4.979 Mbps; mean 10000.0 messages sent and 4862.3 delivered. 0/3 runs delivered every complete sent message; 0/3 delivered the full requested count within the observation window.

## Interpretation limits

A missing TCP message is undelivered at the finite observation cutoff; it does not establish permanent TCP loss. A run can stop generating before the requested count because of duration or backpressure. Zero deliveries produce missing latency, never zero latency. UDP does not have transport retransmissions. Packet loss settings apply independently to received link packets in both directions, including ACKs. Large UDP messages can fragment. CPU cost is not measured; simulator wall time is not endpoint CPU usage.

Random run numbers differ across repetitions. Multiple protocols and conditions share run numbers for reproducibility, not identical packet loss sequences. Conclusions apply only to the configured topology and workload.