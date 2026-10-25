// Paced, framed application traffic through a real ns-3 TCP/UDP stack.
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/traffic-control-module.h"
#ifdef HAVE_NETANIM
#include "ns3/netanim-module.h"
#endif
#include <fstream>
#include <iomanip>
#include <algorithm>
#include <set>
#include <vector>
#include <memory>
using namespace ns3;

static std::ofstream events;
static uint64_t receivedBytes = 0, retransmissions = 0, retransmittedBytes = 0;
static uint64_t highestEnd = 0;
static std::set<uint32_t> received;
static double lastDelivery = 0;
static std::ofstream packets;
static uint64_t packetTraceLimit = 50000, packetTraceCount = 0, omittedPackets = 0;
// Actual device events, independent of application messages and TCP segment traces.
struct PacketContext {
    std::string kind; uint32_t link,source,target;
    bool operator==(const PacketContext& other) const {
        return kind==other.kind && link==other.link && source==other.source && target==other.target;
    }
    bool operator!=(const PacketContext& other) const { return !(*this==other); }
};
static void PacketEvent(PacketContext context, Ptr<const Packet> packet) {
    if (packetTraceCount >= packetTraceLimit) { ++omittedPackets; return; }
    ++packetTraceCount;
    std::string transport="other", detail="";
    uint32_t sequence=0, ack=0;
    auto copy=packet->Copy();
    PppHeader ppp;
    if (copy->GetSize()>=2 && copy->RemoveHeader(ppp) && ppp.GetProtocol()==0x0021) {
        Ipv4Header ip;
        if (copy->GetSize()>=20 && copy->RemoveHeader(ip)) {
            if (ip.GetProtocol()==6 && ip.GetFragmentOffset()==0 && copy->GetSize()>=20) {
                TcpHeader tcpHeader; copy->RemoveHeader(tcpHeader);
                transport="TCP"; sequence=tcpHeader.GetSequenceNumber().GetValue();
                ack=tcpHeader.GetAckNumber().GetValue();
                uint8_t flags=tcpHeader.GetFlags();
                detail=(flags&TcpHeader::SYN) ? ((flags&TcpHeader::ACK) ? "SYN-ACK":"SYN") :
                    (flags&TcpHeader::FIN) ? "FIN" : (flags&TcpHeader::RST) ? "RST" :
                    copy->GetSize() ? "DATA" : "ACK";
            } else if (ip.GetProtocol()==17) { transport="UDP"; detail="DATA"; }
        }
    }
    packets << Simulator::Now().GetSeconds() << ',' << context.kind << ',' << context.link << ',' << context.source << ',' << context.target
        << ',' << packet->GetUid() << ',' << packet->GetSize() << ',' << transport << ',' << detail
        << ',' << sequence << ',' << ack << '\n';
}
static void KeepDeviceQueueRunning(Ptr<NetDeviceQueue> queue, Ptr<const Packet>) { queue->Start(); }
static void DisableDeviceFlowControl(Ptr<PointToPointNetDevice> device) {
    auto interface=device->GetObject<NetDeviceQueueInterface>();
    if (!interface) return;
    auto txQueue=interface->GetTxQueue(0);
    auto queue=device->GetQueue();
    // These callbacks run after NS-3's own callbacks. Keep accepting packets so
    // capacity overflow is handled by DropTail instead of a stopped interface.
    queue->TraceConnectWithoutContext("Enqueue",MakeBoundCallback(&KeepDeviceQueueRunning,txQueue));
    queue->TraceConnectWithoutContext("DropBeforeEnqueue",MakeBoundCallback(&KeepDeviceQueueRunning,txQueue));
    txQueue->Start();
}
static void LogMetric(const std::string& kind, uint64_t seq, double value) {
    events << Simulator::Now().GetSeconds() << ',' << kind << ',' << seq << ',' << value << '\n';
}
static void Cwnd(uint32_t, uint32_t value) { LogMetric("cwnd_bytes", 0, value); }
static void Rtt(Time, Time value) { LogMetric("rtt_ms", 0, value.GetSeconds()*1000); }
static void Tx(Ptr<const Packet> p, const TcpHeader& h, Ptr<const TcpSocketBase>) {
    if (!p->GetSize()) return;
    uint64_t start = h.GetSequenceNumber().GetValue(), end = start + p->GetSize();
    if (start < highestEnd) {
        ++retransmissions;
        retransmittedBytes += std::min(end, highestEnd)-start;
        LogMetric("retransmit_bytes", start, std::min(end, highestEnd)-start);
    }
    highestEnd = std::max(highestEnd, end);
}
static void Rx(Ptr<const Packet> p, const Address&, const Address&, const SeqTsSizeHeader& h) {
    if (!received.insert(h.GetSeq()).second) return;
    receivedBytes += p->GetSize();
    lastDelivery = Simulator::Now().GetSeconds();
    LogMetric("delivery_ms", h.GetSeq(), (Simulator::Now()-h.GetTs()).GetSeconds()*1000);
    LogMetric("received_bytes", h.GetSeq(), p->GetSize());
}

class Source : public Application {
public:
    Ptr<Socket> socket;
    Address peer;
    uint32_t payload = 1024, limit = 1000, sent = 0;
    double rate = 5, deadline = 11;
private:
    Ptr<Packet> pending;
    EventId next;
    bool active = false;
    void StartApplication() override {
        active = true;
        socket->Bind();
        if (!DynamicCast<UdpSocket>(socket))
            socket->SetConnectCallback(MakeCallback(&Source::Connected, this), MakeCallback(&Source::Failed, this));
        socket->SetSendCallback(MakeCallback(&Source::Writable, this));
        socket->Connect(peer);
        if (DynamicCast<UdpSocket>(socket)) Pump();
    }
    void Connected(Ptr<Socket>) { Pump(); }
    void Failed(Ptr<Socket>) { active = false; LogMetric("connection_failed", 0, 1); }
    void Writable(Ptr<Socket>, uint32_t) {
        if (active && pending) Simulator::ScheduleNow(&Source::Resume, this);
    }
    void Resume() { if (pending) Pump(); }
    void Pump() {
        if (!active || Simulator::Now().GetSeconds() >= deadline || sent >= limit) return;
        if (!pending) {
            SeqTsSizeHeader header;
            header.SetSeq(sent);
            header.SetSize(payload + header.GetSerializedSize());
            pending = Create<Packet>(payload);
            pending->AddHeader(header);
            LogMetric("enqueue", sent, payload);
        }
        int accepted = socket->Send(pending);
        if (accepted <= 0) return;
        pending->RemoveAtStart(accepted);
        if (pending->GetSize()) return;
        pending = nullptr;
        LogMetric("sent", sent++, payload);
        next = Simulator::Schedule(Seconds((payload+20)*8/(rate*1e6)), &Source::Pump, this);
    }
    void StopApplication() override {
        active = false;
        Simulator::Cancel(next);
        // Close drains accepted TCP data while the simulation continues.
        socket->Close();
    }
};

int main(int argc, char** argv) {
    std::string protocol = "TCP", output = "run", tcp = "TcpNewReno", topology;
    uint32_t size = 1024, count = 10000, seed = 1, run = 1, queue = 100;
    double duration = 5, drain = 3, delay = 10, loss = 0, bandwidth = 10, rate = 20;
    bool pcap = false, netanim = false;
    CommandLine cmd;
    cmd.AddValue("protocol", "TCP or UDP", protocol);
    cmd.AddValue("size", "Application payload bytes (excluding framing)", size);
    cmd.AddValue("count", "Maximum messages", count);
    cmd.AddValue("duration", "Traffic generation window seconds", duration);
    cmd.AddValue("drain", "Extra receive window seconds", drain);
    cmd.AddValue("delay", "One-way propagation milliseconds", delay);
    cmd.AddValue("loss", "Independent receive packet loss percent, both directions", loss);
    cmd.AddValue("bandwidth", "Link capacity Mbps per direction", bandwidth);
    cmd.AddValue("rate", "Offered framed application rate Mbps", rate);
    cmd.AddValue("queue", "DropTail queue packets per direction", queue);
    cmd.AddValue("seed", "Random seed", seed);
    cmd.AddValue("run", "Independent RNG run", run);
    cmd.AddValue("tcp", "TcpNewReno or TcpCubic", tcp);
    cmd.AddValue("output", "Output path prefix", output);
    cmd.AddValue("pcap", "Write packet captures", pcap);
    cmd.AddValue("topology", "Validated topology interchange file", topology);
    cmd.AddValue("packetTraceLimit", "Maximum device event rows (0 disables capture)", packetTraceLimit);
    cmd.AddValue("netanim", "Export optional NetAnim XML", netanim);
    cmd.Parse(argc, argv);
    NS_ABORT_MSG_IF((protocol!="TCP" && protocol!="UDP") || size<1 || size>8192 || !count ||
        duration<=0 || drain<=0 || delay<0 || loss<0 || loss>=100 || bandwidth<=0 || rate<=0 ||
        !queue || (tcp!="TcpNewReno" && tcp!="TcpCubic"), "Invalid experiment parameters");
    RngSeedManager::SetSeed(seed); RngSeedManager::SetRun(run);
    Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(TypeId::LookupByName("ns3::"+tcp)));
    Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1448));
    events.open(output+"-events.csv");
    NS_ABORT_MSG_IF(!events, "Cannot open event file");
    events << std::setprecision(12) << "time_s,event,sequence,value\n";
    packets.open(output+"-packets.csv");
    NS_ABORT_MSG_IF(!packets, "Cannot open packet trace");
    packets << std::setprecision(12) << "time_s,event,link,source,target,uid,bytes,protocol,detail,sequence,ack\n";
    struct Edge { uint32_t a,b; double bandwidth,delay,loss; uint32_t queue; };
    uint32_t nodeCount=2, edgeCount=1, sender=0, receiver=1;
    std::vector<std::pair<double,double>> positions={{0,50},{100,50}};
    std::vector<Edge> edges={{0,1,bandwidth,delay,loss,queue}};
    if (!topology.empty()) {
        std::ifstream input(topology);
        NS_ABORT_MSG_IF(!(input>>nodeCount>>edgeCount>>sender>>receiver) || nodeCount<2 || nodeCount>32 ||
            !edgeCount || edgeCount>64 || sender>=nodeCount || receiver>=nodeCount || sender==receiver,"Invalid topology header");
        positions.resize(nodeCount); edges.resize(edgeCount);
        for (auto& pos:positions) NS_ABORT_MSG_IF(!(input>>pos.first>>pos.second),"Invalid node position");
        for (auto& edge:edges) {
            NS_ABORT_MSG_IF(!(input>>edge.a>>edge.b>>edge.bandwidth>>edge.delay>>edge.loss>>edge.queue) ||
                edge.a>=nodeCount || edge.b>=nodeCount || edge.a==edge.b || edge.bandwidth<=0 || edge.delay<0 ||
                edge.loss<0 || edge.loss>=100 || !edge.queue,"Invalid topology link");
        }
    }
    NodeContainer nodes; nodes.Create(nodeCount);
    InternetStackHelper internet; internet.Install(nodes);
    Ipv4AddressHelper addresses; addresses.SetBase("10.1.0.0", "255.255.255.252");
    for (uint32_t index=0; index<edges.size(); ++index) {
        const auto& edge=edges[index];
        PointToPointHelper link;
        link.SetDeviceAttribute("DataRate", DataRateValue(DataRate(uint64_t(edge.bandwidth*1e6))));
        link.SetChannelAttribute("Delay", TimeValue(MilliSeconds(edge.delay)));
        link.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", QueueSizeValue(QueueSize(std::to_string(edge.queue)+"p")));
        auto devices=link.Install(nodes.Get(edge.a),nodes.Get(edge.b));
        for (uint32_t i=0;i<2;++i) {
            auto error=CreateObject<RateErrorModel>();
            error->SetAttribute("ErrorUnit",EnumValue(RateErrorModel::ERROR_UNIT_PACKET));
            error->SetAttribute("ErrorRate",DoubleValue(edge.loss/100));
            error->AssignStreams(10+2*index+i);
            auto device=DynamicCast<PointToPointNetDevice>(devices.Get(i));
            // Bypass helper-installed device flow control. Overflow should
            // be dropped by our explicit queue, where it can be measured.
            // NS-3 connects flow-control callbacks during initialization at t=0.
            // Override its stop decisions after initialization, before t=1 traffic.
            Simulator::Schedule(Seconds(0.5),&DisableDeviceFlowControl,device);
            device->SetAttribute("ReceiveErrorModel",PointerValue(error));
            if (packetTraceLimit) {
                uint32_t a=i==0 ? edge.a:edge.b, b=i==0 ? edge.b:edge.a;
                device->TraceConnectWithoutContext("PhyTxBegin",MakeBoundCallback(&PacketEvent,PacketContext{"tx",index,a,b}));
                // MacRx supplies the intact PPP frame after the receive error check.
                device->TraceConnectWithoutContext("MacRx",MakeBoundCallback(&PacketEvent,PacketContext{"rx",index,b,a}));
                device->TraceConnectWithoutContext("PhyRxDrop",MakeBoundCallback(&PacketEvent,PacketContext{"rx_drop",index,b,a}));
                device->GetQueue()->TraceConnectWithoutContext("Drop",MakeBoundCallback(&PacketEvent,PacketContext{"queue_drop",index,a,b}));
            }
        }
        addresses.Assign(devices); addresses.NewNetwork();
        TrafficControlHelper traffic; traffic.Uninstall(devices);
        if (pcap) link.EnablePcap(output+"-link-"+std::to_string(index),devices,false);
    }
    Ipv4GlobalRoutingHelper::PopulateRoutingTables();
#ifdef HAVE_NETANIM
    std::unique_ptr<AnimationInterface> animation;
    if (netanim) {
        for (uint32_t i=0;i<nodeCount;++i)
            AnimationInterface::SetConstantPosition(nodes.Get(i),positions[i].first,positions[i].second);
        animation=std::make_unique<AnimationInterface>(output+"-animation.xml");
        animation->EnablePacketMetadata(true);
        for (uint32_t i=0;i<nodeCount;++i)
            animation->UpdateNodeDescription(i,i==sender ? "Sender":i==receiver ? "Receiver":"Router "+std::to_string(i));
        animation->SetStopTime(Seconds(1+duration+drain));
    }
#else
    NS_ABORT_MSG_IF(netanim,"NetAnim module unavailable in this build. Use built-in packet playback or rebuild with the NS-3 netanim module installed.");
#endif
    std::string factory = protocol=="TCP" ? "ns3::TcpSocketFactory" : "ns3::UdpSocketFactory";
    PacketSinkHelper sink(factory, InetSocketAddress(Ipv4Address::GetAny(), 9000));
    sink.SetAttribute("EnableSeqTsSizeHeader", BooleanValue(true));
    auto sinks = sink.Install(nodes.Get(receiver)); sinks.Start(Seconds(0));
    sinks.Get(0)->TraceConnectWithoutContext("RxWithSeqTsSize", MakeCallback(&Rx));
    auto source = CreateObject<Source>();
    source->socket = Socket::CreateSocket(nodes.Get(sender), TypeId::LookupByName(factory));
    source->peer = InetSocketAddress(nodes.Get(receiver)->GetObject<Ipv4>()->GetAddress(1,0).GetLocal(), 9000);
    source->payload=size; source->limit=count; source->rate=rate; source->deadline=1+duration;
    if (protocol=="TCP") {
        source->socket->TraceConnectWithoutContext("CongestionWindow", MakeCallback(&Cwnd));
        source->socket->TraceConnectWithoutContext("RTT", MakeCallback(&Rtt));
        source->socket->TraceConnectWithoutContext("Tx", MakeCallback(&Tx));
    }
    nodes.Get(sender)->AddApplication(source);
    source->SetStartTime(Seconds(1)); source->SetStopTime(Seconds(1+duration));
    Simulator::Stop(Seconds(1+duration+drain)); Simulator::Run();
    std::ofstream summary(output+"-summary.json");
    summary << std::setprecision(12) << "{\"messages_sent\":" << source->sent << ",\"messages_received\":" << received.size()
        << ",\"bytes_received\":" << receivedBytes << ",\"retransmissions\":" << retransmissions
        << ",\"retransmitted_bytes\":" << retransmittedBytes << ",\"last_delivery_s\":" << lastDelivery
        << ",\"packet_trace_rows\":" << packetTraceCount << ",\"packet_trace_truncated\":" << (omittedPackets ? "true":"false")
        << ",\"packet_trace_omitted\":" << omittedPackets << "}\n";
    Simulator::Destroy();
}
