# The redesigned workflow

Restart Streamlit after pulling changes so imported modules and theme settings reload:

```bash
python -m streamlit run dashboard/app.py
```

- **Overview**: reference-inspired landing page and entry to the lab.
- **Simulation lab**: choose/edit the graph, inspect traffic settings and click **Run simulation**. NS-3 creates new device events; the matching replay opens automatically. The same run selector controls playback, TCP signals and metrics.
- **Archive**: inspect saved batches with recording availability. Raw packet CSVs regenerate players using the current UI, even when cached HTML is absent or outdated. Legacy runs without device events cannot be reconstructed from aggregate metrics; rerun their configuration to create new measurements. Regenerated batches link back to their source batches.
- **Guide**: native Mac setup and measurement definitions.

The original Build your topology canvas was deliberately a static preview, but it misleadingly displayed disabled player controls. The replacement shows a clear layout-only state before simulation and provides the Run action in the same workspace. Existing recordings are labeled as saved results; changing traffic settings requires another run.

## Repair older captures

```bash
python scripts/repair_recordings.py       # preview missing configurations
python scripts/repair_recordings.py --run # run each unique saved configuration once
```

Identical saved configurations share a regenerated batch. Original results remain unchanged. The new manifest identifies source batches and records the current source/binary hashes and configuration. A regenerated experiment is a fresh measurement, not the original packet history.

## Consolidation

- Removed the duplicate static player and sidebar Run action.
- Combined packet/TCP run selectors into one run inspector.
- Removed redundant global link defaults from the visible controls; link tables own bandwidth/delay/base loss/queue.
- Centralized recording discovery and recovery in dashboard/archive.py and rendering in dashboard/run_view.py.
- Converted root C header copies into compatibility includes of common/, so API definitions have one source.
- Retained the legacy experiment YAML/C scaffolding for compatibility; the current NS-3 configuration files are documented in README.md.

Typography is self-hosted. Motion respects reduced-motion settings. Paused players and layout previews do not run continuous rendering loops. Packet capture limits and raw-event text alternatives remain visible.
