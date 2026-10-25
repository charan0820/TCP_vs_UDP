# Recorded routed-network example

Open tcp-impaired.html or udp-impaired.html directly in any browser. They embed real NS-3 device events and the topology; no server, Python, Qt, NetAnim or NS-3 installation is needed for replay.

These are runs 3 and 7 of the eight-run batch in manifest.json, generated with config/topology-demo.yaml. The manifest records source/binary hashes and NS-3 version. results.csv/report.md cover the complete batch. Full traces and PCAP remain in the local Git-ignored data/runs/20261022T111417Z-99448b/ directory.

The player is a recording, not a live simulator. Editing a graph requires a new simulation. Its capture/sampling limits are shown in the player and documented in docs/topologies.md. topology.json is the resolved impaired-run graph for reference; it includes the condition's loss. For a fresh clean/impaired comparison use the base graph in config/topology-demo.yaml, rather than adding impairment twice to that resolved graph.
