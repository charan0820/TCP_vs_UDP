# Measurement contract

- **Network:** two IPv4 nodes, full-duplex point-to-point link and finite DropTail queues. A sender exceeding capacity can congest this link. Competing routed flows remain future work.
- **Workload:** sequence-numbered timestamped messages using NS-3 SeqTsSizeHeader (20-byte framing). Payload size excludes framing. TCP messages are counted after reassembly. Large UDP messages can fragment at IP.
- **Generation:** begins at simulation second 1, after connection for TCP. Each complete accepted frame schedules the next send after framed size / offered rate. TCP backpressure can reduce actual offered traffic. Generation stops at count or duration. Partial frames at cutoff are excluded from complete-message metrics. This is not an always-full-buffer saturation benchmark.
- **Goodput:** delivered payload bytes × 8 / (generation + drain seconds) / 1,000,000. The common fixed observation window includes idle time on short transfers. Last-delivery elapsed time is exported separately. This is not instantaneous link utilization.
- **Delivery delay:** message creation to complete receiver delivery on the shared simulator clock. Includes buffering, retransmission and reassembly. Mean/min/max/median/interpolated p95 use delivered messages only. This is one-way application delay, not echo RTT.
- **RTT:** separately recorded TCP smoothed transport RTT. Do not directly compare it with UDP one-way delay.
- **Jitter:** mean absolute difference of consecutive message delays in receive order. Undefined below two samples. Zero deliveries yield null latency, not zero.
- **Loss:** schema field `packet_loss_percent` means complete sent messages undelivered by cutoff / complete sent messages × 100. This is not link loss. Configured independent receive errors apply to packets in both directions, including TCP ACKs. Queue drops can also occur.
- **Retransmissions:** outgoing TCP data segments overlapping previously transmitted sequence space, plus overlapping bytes. SYN/FIN/ACK-only packets are excluded. Data volume is capped below sequence wrap. UDP retransmissions are undefined (null).
- **Completion:** requested count fully sent and delivered before cutoff. TCP reliability does not guarantee deadline completion.
- **Statistics:** fixed seed, independent RNG run numbers, explicit error-model streams. Groups preserve all workload/network settings. Deterministic clean repetitions can match. Exported report uses population std. P95 of run means differs from per-run p95 message delays.
- **Provenance:** unique batch/run IDs; manifest includes configuration, timestamp, NS-3 version and source SHA-256. Mock results never enter measured batches. CPU is unmeasured; simulator runtime is not endpoint CPU.

Topologies can now be edited with node/link tables. See docs/topologies.md for routed networks, per-link overrides, packet capture limits and event definitions. The original two-node setup remains the default for configurations without a topology block. Existing C socket code is a separate foundation. Findings describe this simulated workload and topology; they do not establish universal protocol rankings.
