# Mac M4 quickstart

Before moving machines, commit/push the source on a feature branch (for example codex/packet-topologies), then clone that branch on the Mac. build/, .venv/ and raw data/runs/ are ignored; the small results/topology-demo/ recording is included for offline playback.

The Mac runs NS-3 natively, without WSL or NS-3 Python bindings. Build on the Mac; do not copy build/ or .venv/ from Windows. Validation here uses Ubuntu/NS-3 3.35; your Mac and NS-3 version still need the test below.

## 1. Expose your existing NS-3 libraries (once)

```bash
brew install cmake pkgconf
pkg-config --list-all | grep ns3
```

If modules appear, proceed to step 2. Otherwise, from your existing modern NS-3 source directory:

```bash
cd /actual/path/to/your/ns-3
./ns3 configure --prefix="$HOME/.local/ns3"
./ns3 build
./ns3 install
export NS3_PREFIX="$HOME/.local/ns3"
```

Keep that export in each Terminal session, or add it to ~/.zshrc. The adapter uses NS3_PREFIX to locate pkg-config metadata. Required modules: core, network, internet, point-to-point, applications, traffic-control. NetAnim is optional.

## 2. Clone, build and run

```bash
git clone <your-repository-url>
cd <repository-folder>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build_ns3.py
python -m experiments.experiment_runner --config config/topology-demo.yaml
python -m streamlit run dashboard/app.py
```

Open http://127.0.0.1:8501. Later: git pull, activate the environment, rebuild if C++ changed, start Streamlit.

## 3. Use the editor and player

1. Open **Simulation lab** and select Direct link, Routed bottleneck, Star or Diamond under **Build your topology**.
2. Expand **Edit nodes and links** to add/edit/delete rows. Node IDs must be consecutive from 0. Select sender and receiver. X/Y controls drawing; link delay controls simulation.
3. Set each link's Mbps, delay, base loss and queue. Under traffic settings, optionally compare clean and impaired conditions. Impaired-condition loss adds independent errors to every link; clean preserves the base loss.
4. Click **Run simulation**. Each run saves the topology actually simulated, and its packet replay opens in the same workspace. The layout shown before a run is only a preview.
5. Use **Packet replay** to play/pause, scrub, adjust speed and filter data/ACK/handshake/drops. A single run selector also controls **TCP signals** and **Metrics & files**. Intermediate nodes forward packets using shortest-hop IPv4 routes.
6. Download the offline HTML player, packet CSV or topology JSON. Reuse JSON with **Imported JSON**. Enable PCAP in advanced capture settings for Wireshark.

**Archive** shows whether each saved run has packet events. If an older batch has no events, use its rerun action to create a fresh measured recording. Raw runs are Git-ignored, so run experiments on the Mac to populate its archive. To repair older local batches in bulk, preview with `python scripts/repair_recordings.py`, then execute with `python scripts/repair_recordings.py --run`.

To populate playback for **all four built-in presets** (Direct link, Routed bottleneck, Star and Diamond), run:

```bash
python scripts/generate_preset_recordings.py --run
```

This creates 16 measured recordings: TCP and UDP under clean and 2% per-link loss conditions for each topology. Each sends 400 application messages of 1024 bytes at 5 Mbps. The generated configurations live in `config/presets/`. Refresh the dashboard, choose a topology in Simulation lab, then choose its recorded run and press Play. Imported JSON is a custom topology and needs its own run.

The editor uses tables, not drag-and-drop. One flow is supported; other nodes act as routers. Edits apply on the next run, not during playback or simulation. Disconnected graphs and duplicate links are rejected.

## Optional NetAnim XML

Built-in playback needs no extra software. Optional XML export must be explicitly enabled at build time with `python scripts/build_ns3.py --netanim`, using an installation that includes NS-3's netanim module. Then check **Export NetAnim XML**. Ordinary builds do not link NetAnim. Older NS-3 3.35 NetAnim libraries are deliberately disabled because the packaged Wi-Fi dependency crashes before main(). Built-in playback and PCAP work on that version. XML export on newer NS-3 is implemented but has not been tested on this machine.

To build the separate NetAnim viewer on the Mac:

```bash
brew install qt
git clone https://gitlab.com/nsnam/netanim.git
cmake -S netanim -B netanim/build -DCMAKE_PREFIX_PATH="$(brew --prefix qt)"
cmake --build netanim/build --parallel 2
```

Launch the resulting application/executable and open a run's *-animation.xml. [Upstream build instructions](https://gitlab.com/nsnam/netanim)

## Verify

```bash
RUN_NS3_TESTS=1 python -m pytest -q
```

If compilation fails, preserve the first compiler error and your NS-3 VERSION file. Newer NS-3 APIs may require adjustments. The build chooses C++17 for pre-3.36 releases and C++20 otherwise (TRANSPORT_CXX_STANDARD overrides this in CMake).

data/runs/ is Git-ignored. results/topology-demo/ contains a small recorded player you can push and open without NS-3.
