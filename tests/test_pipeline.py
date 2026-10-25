import csv
import json
from pathlib import Path
from unittest.mock import patch
import pytest
import yaml
from analysis.statistics import percentile, summarize
from experiments.experiment_runner import load_plan, run_suite, DEFAULT, validate
from metrics.collector import collect


def settings():
    return load_plan(DEFAULT)[1][0][1]


def test_plan_dimensions_and_unique_runs(tmp_path):
    raw = yaml.safe_load(DEFAULT.read_text())
    raw["experiments"]["packet_sizes"] = [64,1024]
    raw["experiments"]["rates_mbps"] = [1,20]
    path = tmp_path/"plan.yaml"; path.write_text(yaml.safe_dump(raw))
    _, plan = load_plan(path)
    assert len(plan)==48
    assert {s["run"] for _,s in plan}=={1,2,3}
    assert len({(name,json.dumps(s,sort_keys=True)) for name,s in plan})==48


@pytest.mark.parametrize("key,value", [("size",8193),("size",True),("duration",0),("duration",float('nan')),
    ("loss",100),("delay",-1),("protocol","QUIC"),("queue",0),("count",0),("tcp","unknown")])
def test_invalid_parameters(key, value):
    s=settings(); s[key]=value
    with pytest.raises(ValueError): validate(s)


def fixture_trace(prefix, sent=4, delivered=3):
    Path(str(prefix)+"-summary.json").write_text(json.dumps(dict(messages_sent=sent,
        messages_received=delivered, bytes_received=delivered*1024,
        retransmissions=2,retransmitted_bytes=2000,last_delivery_s=2 if delivered else 0)))
    Path(str(prefix)+"-events.csv").write_text("time_s,event,sequence,value\n"+
        "".join(f"{1+i*.1},delivery_ms,{i},{v}\n" for i,v in enumerate([10,20,40][:delivered])))


def test_metrics_and_missing_data(tmp_path):
    prefix=tmp_path/"measured"; fixture_trace(prefix)
    s=settings(); row=collect(prefix,s)
    assert row["packet_loss_percent"]==25
    assert row["throughput_mbps"]==3*1024*8/8/1e6
    assert row["avg_latency_ms"]==pytest.approx(70/3)
    assert row["median_latency_ms"]==20
    assert row["p95_latency_ms"]==38
    assert row["jitter_ms"]==15
    fixture_trace(prefix, sent=0, delivered=0)
    row=collect(prefix,s)
    assert row["packet_loss_percent"] is None
    assert row["avg_latency_ms"] is None
    assert row["jitter_ms"] is None
    s["protocol"]="UDP"
    assert collect(prefix,s)["retransmissions"] is None


def test_statistics():
    summary=summarize([1,2,3,4],"metric")
    assert summary.mean==2.5 and summary.median==2.5
    assert summary.std==pytest.approx(1.1180339887)
    assert percentile([1,2,3,4],95)==pytest.approx(3.85)


def test_failed_batch_retains_manifest(tmp_path):
    destination=tmp_path/"failed"
    with patch("experiments.experiment_runner.Ns3Backend.version",return_value="test-only"), \
         patch("experiments.experiment_runner.Ns3Backend.run",side_effect=RuntimeError("test failure")):
        with pytest.raises(RuntimeError): run_suite(DEFAULT,destination)
    manifest=json.loads((destination/"manifest.json").read_text())
    assert manifest["status"]=="failed" and manifest["completed_runs"]==0
    assert "test failure" in manifest["error"]


def test_report_preserves_different_rates(tmp_path):
    from analysis.report import generate
    prefix=tmp_path/"trace"; fixture_trace(prefix)
    first=collect(prefix,settings()); first["condition"]="clean"
    second=dict(first, rate=1)
    (tmp_path/"results.json").write_text(json.dumps([first,second]))
    summaries=generate(tmp_path)
    assert len([s for s in summaries if s["metric"]=="throughput_mbps"])==2
    assert (tmp_path/"report.md").exists()


def test_dashboard_renders():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"dashboard/app.py")).run(timeout=30)
    assert not app.exception
    assert app.radio[0].value=="Overview"
    assert any("PACKET" in item.value for item in app.markdown)
    app.radio[0].set_value("Simulation lab").run(timeout=30)
    assert not app.exception
    assert app.title[0].value=="Simulation lab"
    assert any(b.label=="Run simulation" for b in app.button)
