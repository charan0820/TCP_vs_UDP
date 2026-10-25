"""Manual graph editing with validated node/link tables and import/export."""
import json
import pandas as pd
import streamlit as st
from experiments.topology import preset, normalize


def editor(capacity, delay):
    with st.container():
        st.subheader("Build your topology")
        choices=["Direct link","Routed bottleneck","Star","Diamond","Imported JSON"]
        choice=st.selectbox("Topology preset",choices,index=choices.index(st.session_state.get("active_topology_preset","Routed bottleneck")),key="topology-preset")
        st.session_state["active_topology_preset"]=choice
        drafts=st.session_state.setdefault("topology_drafts",{})
        if choice=="Imported JSON":
            upload=st.file_uploader("Topology JSON",type=["json"])
            if upload is None and "imported_topology" not in st.session_state:
                st.info("Choose a saved topology JSON file."); return None
            try:
                base=normalize(json.loads(upload.getvalue())) if upload is not None else st.session_state["imported_topology"]
                st.session_state["imported_topology"]=base
            except (ValueError,TypeError) as exc:
                st.error(str(exc)); return None
            identity=choice+str(hash(json.dumps(base,sort_keys=True)))
        else:
            base=preset(choice); identity=choice
        # Keep the data-editor seed stable while its edit patches are mounted.
        # Restore the latest independent draft when navigation unmounts widgets.
        seed_key="editor-seed-"+identity
        if "nodes-"+identity not in st.session_state:
            st.session_state[seed_key]=drafts.get(identity,base)
        base=st.session_state[seed_key]
        links=[]
        for edge in base["links"]:
            edge=dict(edge)
            defaults=dict(bandwidth_mbps=capacity,delay_ms=delay,loss_percent=0.,queue_packets=100)
            if choice=="Routed bottleneck":
                defaults.update(bandwidth_mbps=capacity if edge["source"]==1 else max(100.,capacity))
            values={**defaults,**edge}
            links.append({key:values[key] for key in ("source","target","bandwidth_mbps","delay_ms","loss_percent","queue_packets")})
        with st.expander("Edit nodes and links",expanded=False):
            st.caption("Add or remove rows. Keep node IDs consecutive from 0. X/Y changes layout; delay changes the simulation.")
            st.write("Nodes")
            nodes=st.data_editor(pd.DataFrame(base["nodes"]),num_rows="dynamic",hide_index=True,key="nodes-"+identity,width="stretch")
            st.write("Full-duplex links")
            edges=st.data_editor(pd.DataFrame(links),num_rows="dynamic",hide_index=True,key="links-"+identity,width="stretch")
        a,b=st.columns(2)
        sender=a.number_input("Sender node ID",0,31,int(base["sender"]),key="sender-"+identity)
        receiver=b.number_input("Receiver node ID",0,31,int(base["receiver"]),key="receiver-"+identity)
        try:
            # pandas can promote integer columns to floats when adding rows.
            node_rows=json.loads(nodes.to_json(orient="records")); edge_rows=json.loads(edges.to_json(orient="records"))
            for row in node_rows:
                if isinstance(row.get("id"),(int,float)) and row["id"]==int(row["id"]): row["id"]=int(row["id"])
            for row in edge_rows:
                for key in ("source","target","queue_packets"):
                    if isinstance(row.get(key),(int,float)) and row[key]==int(row[key]): row[key]=int(row[key])
            topology=normalize(dict(nodes=node_rows,links=edge_rows,sender=sender,receiver=receiver))
        except (ValueError,TypeError,OverflowError) as exc:
            st.error(f"Fix the topology before running: {exc}"); return None
        drafts[identity]=topology
        st.caption(f"{len(topology['nodes'])} nodes · {len(topology['links'])} links. Changes take effect when you run the simulation.")
        return topology
