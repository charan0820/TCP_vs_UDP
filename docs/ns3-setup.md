# NS-3 setup and integration

**macOS/Apple Silicon:** follow [Mac quickstart](mac-quickstart.md). NS3_PREFIX points the native adapter to locally installed NS-3 libraries.

Python invokes the C++ `build/transport-lab` executable linked to real NS-3 libraries. Windows runs it through WSL; files are shared via `/mnt/c/...`. Native Linux runs it directly. No NS-3 Python bindings or manually started network server are required.

Validated baseline: **Ubuntu 22.04 and packaged NS-3 3.35**, not the latest NS-3 release. Newer pkg-config names are detected but newer releases are untested.

If WSL is absent, use administrator PowerShell: `wsl --install -d Ubuntu-22.04`, then finish Ubuntu account setup. This machine already has that distribution.

Inside Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y g++ cmake make pkg-config python3 ns3 libns3-dev libsqlite3-dev libgsl-dev
```

From PowerShell in this repository:

```powershell
python -m pip install -r requirements.txt
python scripts/build_ns3.py
python -m experiments.experiment_runner --config config/tcp-demo.yaml
python -m streamlit run dashboard/app.py --server.address 127.0.0.1
```

Select another distribution with `$env:NS3_WSL_DISTRO = "Ubuntu-22.04"`. Linux users run the same Python commands after installing packages. CMake caches OS paths: use separate checkouts/build directories across OS environments.

This project links NS-3 directly with CMake, so the source distribution's `./ns3` wrapper is not required. Do not mix headers and libraries from different installations.

## Compare and sweep

```powershell
python -m experiments.experiment_runner --plan --config config/demo.yaml
python -m experiments.experiment_runner --config config/demo.yaml
python -m pytest -q
```

TCP-only has six runs; comparison has twelve. Edit YAML lists to sweep size, count, duration and rate. Conditions are explicit objects. The old `config/experiments.yaml` remains a legacy draft, not an input for this runner.

Unique `data/runs/<batch>/` folders contain the manifest, raw event CSVs, simulator summaries, results CSV/JSON, grouped statistics, measured PNGs and Markdown report. Failed batches preserve partial measurements. Enable `pcap: true` for Wireshark captures.

## Troubleshooting

- WSL access denied: allow the WSL invocation in your execution environment or run from your own terminal.
- No NS-3 pkg-config modules: install `libns3-dev` in the selected distribution.
- Missing sqlite3/gsl/gslcblas: install `libsqlite3-dev libgsl-dev`.
- No data: build first, then run a suite. Mock results never load automatically.
- Missing TCP messages: check generation count and increase drain time. Deadline non-delivery does not imply permanent TCP loss.

Official references: [installation](https://www.nsnam.org/docs/installation/singlehtml/index.html), [PacketSink](https://www.nsnam.org/doxygen/df/d95/classns3_1_1_packet_sink.html), [TCP tracing](https://www.nsnam.org/doxygen/dc/d2a/classns3_1_1_tcp_socket_base.html).
