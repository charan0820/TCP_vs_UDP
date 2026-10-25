# Initial project assessment

| Area | Initially present | Initially missing |
|---|---|---|
| Networking | TCP server, shared header, socket/timing/CSV helpers | TCP client, UDP endpoints, build target |
| Control | YAML loader, Cartesian condition generator | Execution, pacing, collection, NS-3 |
| Analysis | Statistical helpers, mock generator | Measured reports and charts |
| UI/tests/docs | Empty directories, one-line README | Dashboard, tests, setup instructions |

Original condition IDs omit network settings and can collide. Root headers/YAML duplicate files in common/ and config/. C headers are host-endian and require explicit serialization for heterogeneous hosts. The server is sequential. Cross-machine monotonic timestamps cannot measure one-way latency without synchronization.

The new prototype uses C++ NS-3 simulation, Python execution, raw traces, metrics, CSV/JSON, statistics, report and dashboard. It now includes manually editable routed graphs and recorded packet playback; see docs/topologies.md. Existing POSIX C sources remain a separate host-socket foundation: NS-3 uses its own modeled TCP/UDP stack. Native C clients/UDP, endpoint CPU profiling, request-response latency and competing applications remain extensions.
