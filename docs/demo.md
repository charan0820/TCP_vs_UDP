# Demonstration

1. Build: `python scripts/build_ns3.py`.
2. Run: `python -m experiments.experiment_runner --config config/tcp-demo.yaml`.
3. Start: `python -m streamlit run dashboard/app.py --server.address 127.0.0.1`.
4. Compare TCP clean/lossy goodput, delivery delay and retransmissions.
5. Inspect congestion-window and RTT traces. Clean oversubscription can still cause queue drops.
6. Select both protocols and run clean + impaired. Compare actual sent counts and completion as well as throughput.
7. Download CSV/report; show the manifest for reproducibility.
8. Optionally enable PCAP and inspect the handshake, ACKs and retransmissions in Wireshark.

Avoid saying UDP is always faster or TCP always completes before a deadline. Increase drain time to explore reliability versus timely completion.
