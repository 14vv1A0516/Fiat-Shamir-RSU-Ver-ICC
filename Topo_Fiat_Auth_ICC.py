from mn_wifi.cli import CLI 
from mn_wifi.net import Mininet_wifi 
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mininet.term import makeTerm
import time, os, re

def topology():

    net = Mininet_wifi(controller=RemoteController, accessPoint=OVSKernelAP, link=wmediumd, wmediumd_mode=interference)

    info("Creating nodes ---- \n")

    rsu1 = net.addAccessPoint('RSU1', ssid='SSID_RSU1', mac="56:00:00:00:00:70", dpid='1', cls=OVSKernelAP, mode='g', failMode='secure', range='40', channel=4, position='50,40,0')
    rsu2 = net.addAccessPoint('RSU2', ssid='SSID_RSU2', mac="56:00:00:00:00:80", dpid='2', cls=OVSKernelAP, mode='g', failMode='secure', range='40', channel=4, position='120,40,0')
    
    c1 = net.addController('C1', controller=RemoteController, ip='127.0.0.1', port=6653)

    info("**** Configuring Wifi Nodes \n")
    net.configureWifiNodes()

    info("**** Associating and Creating links \n")
    net.plotGraph(max_x=200, max_y=80)
    info("**** Starting network \n")
    net.build()
    c1.start()
    rsu1.start([c1])
    rsu2.start([c1])

    rsu1.cmd('sudo ifconfig RSU1 10.0.0.100/8')
    rsu2.cmd('sudo ifconfig RSU2 10.0.0.200/8')

    makeTerm (rsu1, cmd = "bash -c 'python3 Auth_RSU1_ICC.py ;'")
    makeTerm (rsu2, cmd = "bash -c 'python3 Auth_RSU2_ICC.py ;'")

    info("**** Running CLI \n")
    CLI(net)

    info("**** Stopping network \n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()