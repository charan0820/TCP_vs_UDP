# Transport Lab

## Platform and stack
Local web application using Python/Streamlit, backed by C++ NS-3. Windows uses Ubuntu WSL; macOS/Linux run natively. Python controls experiments without NS-3 Python bindings.

## Users and task
The user is building a student TCP/UDP performance-evaluation project and needs to configure networks, demonstrate packet transport and compare measured outcomes. They will run the project on a Mac M4 after pushing its source.

## Product truth
One paced flow over a manually editable static point-to-point IPv4 graph. Per-link bandwidth, propagation delay, base loss and queue size; TCP NewReno/Cubic and UDP. Repeated real simulator runs produce raw events, goodput, delivery delay, jitter, finite-window non-delivery and TCP traces. No fabricated results. Archive replay requires real recorded device events; legacy runs without them must be rerun as a new batch.

## Confirmed visual brief
Full UI overhaul guided by the supplied Memory Core reference and Nexus design document: near-black, cyan/violet signal field, Sora/IBM Plex Mono, gradients, colorful panels and smooth motion. Reference text and fictional archive claims are inspiration, not product copy.

## Constraints
Keep the reproducible simulator and Mac workflow. Built-in playback needs no Qt/NetAnim. Preserve archived measurements and disclose missing/capped data. Respect reduced motion and provide text alternatives to canvas. No cloud publishing is requested.
