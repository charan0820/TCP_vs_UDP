"""A single selected run drives recording, TCP traces and metric inspection."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dashboard.archive import recording,prefix_for,topology_for
from visualization.packets import playback_html

MESSAGES={
    "missing":"This run predates packet recording, or its packet CSV was not copied. Metrics are available, but its packet journey cannot be reconstructed from application summaries.",
    "empty":"No device events were captured. Packet capture may have been disabled, or this run sent no packets.",
    "invalid":"The packet recording is incomplete or unreadable. Keep the original measurements and rerun the configuration to create a fresh recording.",
}


def run_label(row):
    return f"{row['protocol']} · {row.get('condition','baseline')} · {row['packet_size']} B · repetition {row.get('run',1)}"


def render(batch,row,autoplay=False,key="recording"):
    prefix=prefix_for(batch,row)
    st.caption(f"NS-3 {row.get('ns3_version',batch['manifest'].get('ns3_version','unknown'))} · {run_label(row)}")
    replay,signals,details=st.tabs(["Packet replay","TCP signals","Metrics & files"])
    with replay:
        html,status=recording(batch,row,autoplay)
        if html:
            components.html(html,height=580,scrolling=True)
            st.download_button("Save offline replay",html,"packet-replay.html","text/html",key=key+"-html")
        else:
            st.warning(MESSAGES[status])
            try: components.html(playback_html(topology_for(batch,row)),height=340,scrolling=True)
            except (KeyError,ValueError,OSError): st.caption("Topology data is also unavailable for this run.")
        if row.get("packet_trace_truncated"): st.warning("Capture reached its event limit. Later packet outcomes may be missing; metrics still use the full observation window.")
        packet=Path(str(prefix)+"-packets.csv")
        if packet.exists():
            with st.expander("Inspect recorded packet events"):
                try: st.dataframe(pd.read_csv(packet).head(1000),hide_index=True,width="stretch")
                except (pd.errors.ParserError,pd.errors.EmptyDataError): st.error("Packet CSV could not be parsed.")
                st.caption("Preview: first 1,000 events. The download contains every captured event.")
                st.download_button("Download packet CSV",packet.read_bytes(),"packets.csv","text/csv",key=key+"-csv")
    with signals:
        events=Path(str(prefix)+"-events.csv")
        if row["protocol"]!="TCP": st.info("UDP has no TCP congestion window, transport RTT or retransmission trace. Inspect its packet replay and delivery metrics instead.")
        elif not events.exists(): st.info("The TCP event file was not copied with this batch. Rerun it to record new traces.")
        else:
            frame=pd.read_csv(events)
            for event,label in [("cwnd_bytes","Congestion window / bytes"),("rtt_ms","Smoothed transport RTT / ms"),("retransmit_bytes","Retransmitted data / bytes")]:
                st.write(label)
                values=frame[frame.event==event]
                if values.empty: st.caption("No events of this type were recorded.")
                else: st.line_chart(values.set_index("time_s")[["value"]],color="#A78BFA")
    with details:
        columns=st.columns(2)
        for i,(field,label,unit) in enumerate([("throughput_mbps","Payload goodput","Mbps"),("avg_latency_ms","Application delay","ms"),("jitter_ms","Jitter","ms"),("packet_loss_percent","Undelivered at cutoff","%")]):
            value=row.get(field)
            columns[i%2].metric(label,"Unavailable" if value is None else f"{value:.3f} {unit}")
        st.caption(f"{row.get('messages_received',0):,} complete messages delivered / {row.get('messages_sent',0):,} sent. Goodput uses generation + drain time; application delay is one-way, not RTT.")
        with st.expander("All run measurements"): st.json(row)
        base=batch["manifest"].get("configuration",{}).get("topology")
        if base: st.download_button("Export editable topology",json.dumps(base,indent=2),"topology.json","application/json",key=key+"-topology")
        for suffix,label,mime in [("-animation.xml","Download NetAnim XML","application/xml"),("-summary.json","Download simulator summary","application/json")]:
            file=Path(str(prefix)+suffix)
            if file.exists(): st.download_button(label,file.read_bytes(),file.name,mime,key=key+suffix)
    return status

