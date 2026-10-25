# Topology and recording contract

Topology JSON/YAML contains nodes (id, label, x, y), full-duplex links (source, target, optional bandwidth_mbps/delay_ms/loss_percent/queue_packets), sender and receiver. See config/topology-demo.yaml. Limits: 2–32 nodes, 1–64 links, connected graph, consecutive integer IDs. Missing capacity/delay/queue inherit experiment settings. Base link loss defaults to zero; base probability p and condition probability q combine as 1-(1-p)(1-q), independently per received packet, per link and direction.

Each link has a separate /30 IPv4 subnet. Global routing chooses shortest-hop paths before simulation. All intermediate nodes can forward. Coordinates affect only the drawing; unused links in a diamond are expected. One flow does not automatically spread over every route. Default root queue discs are removed and device flow-control stop decisions are overridden after initialization, so overflow reaches the configured DropTail queue and is recorded there.

Per-run files: *-topology.json (resolved graph), *-topology.txt (simulator input), *-packets.csv (actual device events), *-playback.html (self-contained player). topology_id hashes the resolved graph and is included in statistical grouping. Original configuration remains in manifest.json.

Events: PhyTxBegin (tx), successful MacRx (rx), PhyRxDrop (rx_drop), queue Drop (queue_drop). Fields include timestamp, link/direction, packet UID, bytes including headers, protocol, TCP control type, sequence and ACK numbers. A UID is not an application message ID; a routed packet can keep its UID across hops. Non-initial fragments lack a transport header and are not parsed as TCP headers.

TX is paired with RX/error on the same UID/link/direction. Missing outcomes stay **unobserved**. Queue drops have no transit. Markers/drop flashes are visually enlarged; event timestamps are measured. At most 200 active markers render at once. The exact stream remains in the downloadable CSV.

Default capture: 50,000 event rows/run. Summary marks packet_trace_truncated and counts omitted events. Metrics and optional PCAP/NetAnim are independent of this limit. Built-in HTML embeds up to the first 3,000 transmissions/drop markers. Change packet_trace_limit in YAML or the sidebar. Zero disables packet recording via CLI.

Scope: static point-to-point IPv4 graphs, one paced sender/receiver flow. Wireless, competing applications, dynamic routing failures and edits during simulation are not implemented.
