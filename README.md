# Transport Lab — TCP / UDP Performance Evaluation

C++ NS-3 simulations with Python automation, measured reports and a local dashboard. The prototype demonstrates TCP reliability and congestion control, with UDP as a controlled comparison.

```text
YAML → Python runner → C++ NS-3 network/transport stack
                                ↓
                        Raw message + TCP traces
                                ↓
                 CSV/JSON → statistics → report/dashboard
```

Windows invokes NS-3 in Ubuntu WSL. NS-3 provides the modeled transport stack; existing POSIX C sources are a separate host-socket foundation.

## Run

**Mac M4:** follow [Mac quickstart](docs/mac-quickstart.md). Built-in packet playback needs no NetAnim installation.

Follow [NS-3 prerequisites](docs/ns3-setup.md), then:

```powershell
python -m pip install -r requirements.txt
python scripts/build_ns3.py
python -m experiments.experiment_runner --config config/tcp-demo.yaml
python -m streamlit run dashboard/app.py --server.address 127.0.0.1
```

Use `config/demo.yaml` for both protocols. Add `--plan` to preview a suite. Unique `data/runs/` batches contain measured events, CSV/JSON, statistics, PNG graphs and Markdown report. No synthetic data is loaded into the dashboard.

## Features

The redesigned interface starts with **Overview**, then a unified **Simulation lab**, **Archive**, and **Guide**. See [UI workflow and recording repair](docs/ui-workflow.md). Restart the Streamlit process after updating the code and theme.

- C++ framed/paced message traffic over real NS-3 TCP/UDP models.
- Configurable size/count/duration/rate, capacity/delay/loss/queue, seed/repetitions and NewReno/Cubic.
- Complete-message goodput, delivery delay distribution, jitter and finite-window non-delivery.
- TCP congestion-window, RTT and retransmission traces; optional Wireshark PCAP.
- Reproducible experiments, provenance manifests, statistics, reports and dashboard controls/downloads.
- Manual topology editor with node/link tables, sender/receiver selection, per-link parameters, JSON import/export and direct/routed/star/diamond presets.
- Recorded packet playback with timeline, speed, packet filters and offline HTML download; optional NetAnim XML export.

## Structure

| Directory | Responsibility |
|---|---|
| simulation/ | C++ model, sender and tracing |
| experiments/ | Validation, WSL/Linux adapter, execution |
| metrics/ | Event reduction |
| analysis/ | Statistics, report and measured figures |
| dashboard/ | Streamlit workbench |
| config/ | Demo suites; older experiments.yaml is a legacy draft |
| client/, server/, common/ | Original separate POSIX socket foundation |
| tests/ | Configuration, metrics and integration checks |

[Initial assessment](docs/current-state.md) · [Setup](docs/ns3-setup.md) · [Metric definitions](docs/methodology.md) · [Demo](docs/demo.md)

Latency is one-way application delivery delay; transport RTT is separately traced. `packet_loss_percent` means messages undelivered at cutoff, not lost TCP segments. Throughput is observation-window payload goodput.

Use config/topology-demo.yaml for a routed bottleneck demonstration. See [topology and recording definitions](docs/topologies.md). Native C clients/UDP, request-response latency, endpoint CPU profiling and competing flows remain extensions. Root headers/YAML and config/experiments.yaml are retained legacy drafts.

```powershell
python -m pytest -q
```
