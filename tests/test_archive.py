import json
from pathlib import Path
from unittest.mock import patch
import pytest
from experiments.topology import preset,resolve
from dashboard.archive import batches,prefix_for,recording,availability,latest_matching,rerun_configuration,regenerated_for


def fixture_batch(tmp_path,topology=None,packets=True):
    folder=tmp_path/"batch-01";folder.mkdir()
    row=dict(experiment_id="batch-01-0003",protocol="TCP",condition="baseline",packet_size=64,
        size=64,count=5,packet_count=5,duration=2,drain=2,rate=1,bandwidth=10,delay=1,loss=0,queue=100,
        run=1,tcp="TcpNewReno",throughput_mbps=.001,avg_latency_ms=1,jitter_ms=0,
        packet_loss_percent=0,retransmissions=0,messages_sent=5,messages_received=5)
    config=dict(topology=topology or preset(),packet_trace_limit=0,netanim=True)
    manifest=dict(configuration=config,status="complete",ns3_version="test-fixture")
    (folder/"manifest.json").write_text(json.dumps(manifest))
    (folder/"results.json").write_text(json.dumps([row]))
    prefix=folder/"run-0003"
    Path(str(prefix)+"-topology.json").write_text(json.dumps(resolve(config["topology"],row)))
    if packets:Path(str(prefix)+"-packets.csv").write_text("time_s,event,link,source,target,uid,bytes,protocol,detail,sequence,ack\n1,tx,0,0,1,1,64,TCP,SYN,0,0\n1.01,rx,0,0,1,1,64,TCP,SYN,0,0\n")
    return batches(tmp_path)[0],row,prefix


def test_filtered_rows_keep_actual_run_index(tmp_path):
    batch,row,prefix=fixture_batch(tmp_path)
    assert prefix_for(batch,row)==prefix


def test_missing_cached_html_rebuilds_from_measured_events(tmp_path):
    batch,row,prefix=fixture_batch(tmp_path)
    assert not Path(str(prefix)+"-playback.html").exists()
    html,status=recording(batch,row,autoplay=True)
    assert status=="ready" and '"autoplay": true' in html
    assert "#05060a" in html


def test_missing_packet_events_are_never_fabricated(tmp_path):
    batch,row,prefix=fixture_batch(tmp_path,packets=False)
    assert recording(batch,row)==(None,"missing")
    Path(str(prefix)+"-packets.csv").write_text("time_s,event,link,source,target,uid,bytes,protocol,detail,sequence,ack\n")
    assert recording(batch,row)==(None,"empty")
    Path(str(prefix)+"-packets.csv").write_text("experiment_id,payload\nold,10\n")
    assert availability(prefix)=="invalid"


def test_draft_does_not_show_another_topologys_recording(tmp_path):
    batch,row,prefix=fixture_batch(tmp_path)
    assert latest_matching([batch],preset()) is not None
    assert latest_matching([batch],preset("Star")) is None


def test_rerun_preserves_old_configuration(tmp_path):
    batch,_,_=fixture_batch(tmp_path)
    config=rerun_configuration(batch)
    assert config["packet_trace_limit"]==50000 and not config["netanim"]
    assert batch["manifest"]["configuration"]["packet_trace_limit"]==0
    assert batch["manifest"]["configuration"]["netanim"]


def test_failed_and_corrupt_batches_remain_inspectable(tmp_path):
    fail=tmp_path/"failed";fail.mkdir()
    (fail/"manifest.json").write_text('{"status":"failed","configuration":{},"error":"test failure"}')
    corrupt=tmp_path/"corrupt";corrupt.mkdir();(corrupt/"manifest.json").write_text("{")
    results=batches(tmp_path)
    assert len(results)==2
    assert any(item["error"] for item in results)
    assert any(item["manifest"].get("status")=="failed" and item["rows"]==[] for item in results)


def test_preview_has_no_disabled_playback_controls():
    from visualization.packets import playback_html
    html=playback_html(resolve(preset(),dict(bandwidth=10,delay=1,queue=100,loss=0)))
    assert ".preview .controls" in html
    assert "play.disabled=true" not in html


def test_run_action_uses_selected_topology():
    from streamlit.testing.v1 import AppTest
    app_path=Path(__file__).resolve().parents[1]/"dashboard/app.py"
    captured=[]
    def stop(config,**kwargs):
        import yaml
        captured.append(yaml.safe_load(Path(config).read_text()))
        raise RuntimeError("Test-only backend stop")
    with patch("experiments.experiment_runner.run_suite",side_effect=stop) as runner:
        app=AppTest.from_file(str(app_path)).run(timeout=30)
        app.radio[0].set_value("Simulation lab").run(timeout=30)
        next(s for s in app.selectbox if s.label=="Topology preset").set_value("Star").run(timeout=30)
        next(b for b in app.button if b.label=="Run simulation").click().run(timeout=30)
        assert not app.exception
        assert runner.call_count==1
        assert len(captured[0]["topology"]["nodes"])==5
        assert captured[0]["topology"]["receiver"]==2
        assert any("Test-only backend stop" in error.value for error in app.error)


def test_identical_legacy_configurations_are_regenerated_once(tmp_path):
    from scripts.repair_recordings import plan
    first,row,_=fixture_batch(tmp_path,packets=False)
    second={**first,"folder":tmp_path/"same-settings"}
    planned=plan([first,second])
    assert len(planned)==1 and len(planned[0]["sources"])==2
    successor=dict(folder=tmp_path/"new",rows=[],manifest=dict(status="complete",replay_of_batches=planned[0]["sources"]))
    assert regenerated_for([successor],first)==successor
    assert not plan([first,second,successor])


def test_topology_draft_survives_navigation():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"dashboard/app.py")).run(timeout=30)
    app.radio[0].set_value("Simulation lab").run(timeout=30)
    next(s for s in app.selectbox if s.label=="Topology preset").set_value("Star").run(timeout=30)
    next(n for n in app.number_input if n.label=="Sender node ID").set_value(1).run(timeout=30)
    next(n for n in app.number_input if n.label=="Offered rate / Mbps").set_value(7.).run(timeout=30)
    app.radio[0].set_value("Overview").run(timeout=30)
    app.radio[0].set_value("Simulation lab").run(timeout=30)
    assert not app.exception
    assert next(s for s in app.selectbox if s.label=="Topology preset").value=="Star"
    assert next(n for n in app.number_input if n.label=="Sender node ID").value==1
    assert next(n for n in app.number_input if n.label=="Offered rate / Mbps").value==7.
