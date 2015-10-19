# Sample Smartenit Client program
# Author: Dhawal Doshi
# Last Edit: Dec 10, 2013
# Built and Tested with Python version 2.7.5

# import modules
import socket
import hashlib
from xml.dom.minidom import parseString
import thread
import time
import os

# Temporary and global variables
HOST = '192.168.142.10'     # IP Address of Smartenit Gateway, Example: '192.168.1.238'
PORT = 50333                # The port used by the Smartenit Gateway, default is 50333
PASSWORD = '1234'      # Password to connect to the Smartenit Gateway.

NODELIST = ""               # List of RecordId of devices in the Gateway, obtained from Node_GetNumNodes
SMARTPLUGS = []             # List of RecordId of Smartplugs
power = ""                  # temporary storage for kw
kwh = ""                    # temporary storage for kwh

POLL_INTERVAL = 30          # Interval in seconds for polling metering information from Smartplugs

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))


# Functions
def connect(HOST, PORT, PASSWORD):
    hash_object = hashlib.sha1(PASSWORD)
    password = hash_object.hexdigest()
    #print(hex_dig)
    s.send('<zbpPacket><Object>ZBP_System</Object><methodName>Sys_Authenticate</methodName><Arguments> \
    <Argument type="string">'+password+'</Argument></Arguments><id>12625</id></zbpPacket>\0')


def getnumnodes():
    s.send('<zbpPacket><Object>ZBP_Node</Object><methodName>Node_GetNumNodes</methodName><Arguments> \
    </Arguments></zbpPacket>\0')


def Node_GetNode(NODEID):
    #node = int(NODEID,16)
    NODEID = str(int(NODEID, 16))
    pkt = '<zbpPacket><Object>ZBP_Node</Object><methodName>Node_GetNode</methodName><Arguments> \
    <Argument type="ushort" base="10">'+NODEID+'</Argument></Arguments><id>1</id></zbpPacket>\0'
    # pkt = '<zbpPacket><Object>ZBP_Node</Object><methodName>Node_GetNode</methodName><Arguments> \
    # <Argument type="ushort">'+NODEID+'</Argument></Arguments></zbpPacket>\0'
    # print '\r\n',pkt
    s.send(pkt)


def Node_ClusterCommand(deviceid):
    #x = int(deviceid, 16)
    #nodeid_dec = str(x)
    s.send('<zbpPacket><Object>ZBP_Node</Object><methodName>Node_ClusterCommand</methodName>\
    <Arguments><Argument type="uchar" base="10">146</Argument><Argument type="ushort" base="10">'
           + str(deviceid) + '</Argument><Argument type="uchar" base="10">2</Argument><Argument type="ushort"\
            base="10">1794</Argument><Argument type="uchar" base="10">0</Argument><Argument type="QByteArray"\
             base="10">[2,0,0,4,0]</Argument></Arguments><id>7</id></zbpPacket>\0')


def getnode_details():
    while True:
        nodes = len(NODELIST)
        if(nodes > 0):
            #print 'Inside getnode_details'
            #print("NodeList: "),NODELIST
            #print("\n")
            for x in NODELIST:
                #print '\nGetting Node: ',x
                Node_GetNode(x)
                time.sleep(0.1)
            break


def poll_smartplugs():
    time.sleep(10)
    while True:
        #print 'Inside poll_smartplugs'
        nodes = len(SMARTPLUGS)
        #print SMARTPLUGS
        #print("\n")
        #print len(SMARTPLUGS)
        if(nodes > 0):
            #print 'Inside poll_smartplugs'
            #print("Smartplugs: "),SMARTPLUGS
            #print("\n")
            for deviceid in SMARTPLUGS:
                print('Getting Metering Information from: ' + str(deviceid) + '\n')
                Node_ClusterCommand(deviceid)
                time.sleep(5)
            #break
            time.sleep(POLL_INTERVAL)


def parseXML(DATA):
    pos = DATA.find("<methodName>")
    if pos != -1:
        pos2 = DATA.find("</methodName>")
        if pos != -1:
            method = DATA[pos+12:pos2]
            #print 'method = ', method
            if method == "Node_GetNumNodes":
                #print 'Found GetNumNodes'
                pos = DATA.find("[")
                if pos != -1:
                    pos2 = DATA.find("]")
                    if pos2 != -1:
                        global NODELIST
                        NODELIST = DATA[pos+1:pos2]
                        NODELIST = NODELIST.split(',')
                        print('\nNodeList Populated: \n', NODELIST)
                        #getnode_details()
            if method == "Node_GetNode":
                pos = DATA.find("ZBMPlug15")
                if pos != -1:
                    print('Found Smartplug: \n')  # ,DATA
                    pos = DATA.find("\x00")
                    #print pos
                    if pos != -1:
                        DATA = DATA[:pos]
                        #print DATA
                        xmldoc = parseString(DATA)
                        args = xmldoc.getElementsByTagName("Argument")
                        #print args
                        deviceid = int(args[1].firstChild.nodeValue, 16)
                        #print deviceid
                        #print("\n")
                        global SMARTPLUGS
                        SMARTPLUGS.append(deviceid)
                        print(SMARTPLUGS)
    pos = DATA.find("<zbpPacketSignal>")
    pos_end = DATA.find("</zbpPacketSignal>")
    if((pos != -1) and (pos_end != -1)):
        DATA = DATA[pos:pos_end+18]
        #print ("Signal Received: '\n'"),DATA
        pos = DATA.find("<signalName>")
        if pos != -1:
            pos2 = DATA.find("</signalName>")
            if pos2 != -1:
                method = DATA[pos+12:pos2]
                #print 'signal = ', method
                if method == "Node_ClusterCmdRsp":
                    pos = DATA.find("\x00")
                    if pos != -1:
                        DATA = DATA[:pos]
                    # DATA = '<zbpPacketSignal><signalName>Node_ClusterCmdRsp</signalName><Arguments>\
                    # <Argument type="uchar">b2</Argument><Argument type="ushort">ff42</Argument>\
                    # <Argument type="uchar">2</Argument><Argument type="ushort">702</Argument>\
                    # <Argument type="uchar">a</Argument><Argument type="uchar">2</Argument>\
                    # <Argument type="QByteArray" length="15">[4,0,2a,0,0,0,0,0,25,0,0,0,0,46,2b]</Argument>\
                    #<Argument type="uchar">2</Argument></Arguments></zbpPacketSignal>'
                    DATA = str(DATA)
                    #print ("Metering Info Received: '\n'"),DATA
                    xmldoc = parseString(DATA)
                    args = xmldoc.getElementsByTagName("Argument")
                    deviceid = int(args[1].firstChild.nodeValue, 16)
                    #print ("Device ID: "),deviceid
                    commandid = int(str(args[4].firstChild.nodeValue), 16)
                    clusterid = int(str(args[3].firstChild.nodeValue), 16)
                    meterdata = str(args[6].firstChild.nodeValue)
                    meterdata = meterdata[1:-1]  # removing []
                    meterdata = meterdata.split(',')
                    #rawmeter = meterdata
                    #print ("Received Raw Data: %s\n") % rawmeter
                    meterdata = [int(i, 16) for i in meterdata]
                    #proc_meterdata = meterdata
                    if(commandid == 1):
                        print("Processing synch response\r")
                        #print "Processing synchronous response: %s\n" % proc_meterdata
                        if(clusterid == 1794):
                            if(len(meterdata) >= 9):
                                for i in range(len(meterdata)):
                                    if(((len(meterdata))-9) >= i):
                                        if ((meterdata[i] == 0)
                                                and (meterdata[i+1] == 0)
                                                and (meterdata[i+2] == 0)
                                                and (meterdata[i+3] == 37)):
                                            byte1 = str(format(meterdata[i+4], 'x'))
                                            if(len(byte1) == 1):
                                                byte1 = '0'+byte1
                                            byte2 = str(format(meterdata[i+5], 'x'))
                                            if(len(byte2) == 1):
                                                byte2 = '0'+byte2
                                            byte3 = str(format(meterdata[i+6], 'x'))
                                            if(len(byte3) == 1):
                                                byte3 = '0'+byte3
                                            byte4 = str(format(meterdata[i+7], 'x'))
                                            if(len(byte4) == 1):
                                                byte4 = '0'+byte4
                                            byte5 = str(format(meterdata[i+8], 'x'))
                                            if(len(byte5) == 1):
                                                byte5 = '0'+byte5
                                            byte6 = str(format(meterdata[i+9], 'x'))
                                            if(len(byte6) == 1):
                                                byte6 = '0'+byte6
                                            global kwh
                                            kwh = float(int(str(byte1+byte2+byte3+byte4+byte5+byte6), 16))
                                            # kwh = float(int(str(format(meterdata[i+4],'x'))+\
                                            # str(format(meterdata[i+5],'x'))+str(format(meterdata[i+6],'x'))\
                                            # +str(format(meterdata[i+7],'x'))\
                                            # +str(format(meterdata[i+8],'x'))\
                                            # +str(format(meterdata[i+9],'x')),16))
                                            kwh = kwh/100000
                                            break
                            if(len(meterdata) >= 6):
                                for k in range(len(meterdata)):
                                    if(((len(meterdata))-6) >= i):
                                        if ((meterdata[k] == 4)
                                                and (meterdata[k+1] == 0)
                                                and (meterdata[k+2] == 0)
                                                and (meterdata[k+3] == 42)):
                                            byte1 = str(format(meterdata[k+4], 'x'))
                                            if(len(byte1) == 1):
                                                byte1 = '0'+byte1
                                            byte2 = str(format(meterdata[k+5], 'x'))
                                            if(len(byte2) == 1):
                                                byte2 = '0'+byte2
                                            byte3 = str(format(meterdata[k+6], 'x'))
                                            if(len(byte3) == 1):
                                                byte3 = '0'+byte3

                                            global power
                                            power = float(int(str(byte1+byte2+byte3), 16))
                                            # power = float(int(str(format(meterdata[k+4],'x'))\
                                            # +str(format(meterdata[k+5],'x'))\
                                            # +str(format(meterdata[k+6],'x')),16))
                                            power = power/100000
                                            break
                            print("{}   {}   {} kW   {} kW\r\n".format(
                                time.ctime(time.time()), deviceid, power, kwh)
                            )
                            output = str(time.ctime(time.time()))+','+str(power)+','+str(kwh)+'\n'
                            filename = str(deviceid) + '.csv'
                            fo = open(filename, "a")
                            fo.seek(0, os.SEEK_END)
                            size = fo.tell()
                            if(size <= 0):
                                fo.write("Time,kW,kWh\n")
                                fo.write(output)
                            else:
                                fo.write(output)
                            fo.close()
                    elif(commandid == 10):
                        print("Processing asynch response\r")
                        #print "Processing asynch resp: %s\n" % proc_meterdata
                        #print "cluster id: %d\r" % clusterid
                        demand_rx = 0
                        kwh_rx = 0
                        write_to_file = 0
                        if(clusterid == 1794):
                            if(len(meterdata) >= 8):
                                for i in range(len(meterdata)):
                                    #print("len: %d, i: %d") % (len(meterdata),i)
                                    if(((len(meterdata))-8) >= i):
                                        if ((meterdata[i] == 0)
                                                and (meterdata[i+1] == 0)and(meterdata[i+2] == 37)):
                                            byte1 = str(format(meterdata[i+3], 'x'))
                                            if(len(byte1) == 1):
                                                byte1 = '0'+byte1
                                            byte2 = str(format(meterdata[i+4], 'x'))
                                            if(len(byte2) == 1):
                                                byte2 = '0'+byte2
                                            byte3 = str(format(meterdata[i+5], 'x'))
                                            if(len(byte3) == 1):
                                                byte3 = '0'+byte3
                                            byte4 = str(format(meterdata[i+6], 'x'))
                                            if(len(byte4) == 1):
                                                byte4 = '0'+byte4
                                            byte5 = str(format(meterdata[i+7], 'x'))
                                            if(len(byte5) == 1):
                                                byte5 = '0'+byte5
                                            byte6 = str(format(meterdata[i+8], 'x'))
                                            if(len(byte6) == 1):
                                                byte6 = '0'+byte6
                                            global kwh
                                            kwh = float(int(str(byte1+byte2+byte3+byte4+byte5+byte6), 16))
                                            # kwh = float(int(str(format(meterdata[i+3],'x'))\
                                            # +str(format(meterdata[i+4],'x'))\
                                            # +str(format(meterdata[i+5],'x'))\
                                            # +str(format(meterdata[i+6],'x'))\
                                            # +str(format(meterdata[i+7],'x'))\
                                            # +str(format(meterdata[i+8],'x')),16))
                                            kwh = kwh/100000
                                            kwh_rx = 1
                                            break
                            if(len(meterdata) >= 5):
                                for k in range(len(meterdata)):
                                    #print("len: %d, k: %d") % (len(meterdata),k)
                                    if(((len(meterdata))-5) >= k):
                                        if ((meterdata[k] == 4)
                                                and(meterdata[k+1] == 0)and(meterdata[k+2] == 42)):
                                            byte1 = str(format(meterdata[k+3], 'x'))
                                            if(len(byte1) == 1):
                                                byte1 = '0'+byte1
                                            byte2 = str(format(meterdata[k+4], 'x'))
                                            if(len(byte2) == 1):
                                                byte2 = '0'+byte2
                                            byte3 = str(format(meterdata[k+5], 'x'))
                                            if(len(byte3) == 1):
                                                byte3 = '0'+byte3

                                            global power
                                            power = float(int(str(byte1+byte2+byte3), 16))
                                            # power = float(int(str(format(meterdata[k+3],'x'))\
                                            # +str(format(meterdata[k+4],'x'))\
                                            # +str(format(meterdata[k+5],'x')),16))
                                            power = power/100000
                                            demand_rx = 1
                                            break

                            if((demand_rx == 1) and (kwh_rx == 1)):
                                print("{}   {}   {} kW   {} kWh\r\n".format(
                                    time.ctime(time.time()), deviceid, power, kwh)
                                )
                                write_to_file = 1
                            elif((demand_rx == 1) and (kwh_rx == 0)):
                                print("{}   {}   {} kW\r\n".format(time.ctime(time.time()), deviceid, power))
                                write_to_file = 1
                                kwh = 0
                            elif((demand_rx == 0) and (kwh_rx == 1)):
                                print("{}   {}   {} kWh\r\n".format(time.ctime(time.time()), deviceid, kwh))
                                write_to_file = 1
                                power = 0
                            if(write_to_file == 1):
                                output = str(time.ctime(time.time()))+','+str(power)+','+str(kwh)+'\n'
                                filename = str(deviceid) + '.csv'
                                fo = open(filename, "a")
                                fo.seek(0, os.SEEK_END)
                                size = fo.tell()
                                if(size <= 0):
                                    fo.write("Time,kW,kWh\n")
                                    fo.write(output)
                                else:
                                    fo.write(output)
                                fo.close()

                            write_to_file = 0
                            demand_rx = 0
                            kwh_rx = 0


# Function for RX Thread
def recvpkt(threadName, delay):
    while True:
        data = s.recv(1024)
        if len(data) > 0:
            #print 'Received: \n', data.__len__(),repr(data)
            parseXML(data)
        else:
            print('Connection Closed, Re-connecting...')
            connect(HOST, PORT, PASSWORD)


#TX Thread
def sendpkt():
    connect(HOST, PORT, PASSWORD)
    time.sleep(5)
    getnumnodes()

# Threads
try:
    thread.start_new_thread(recvpkt, ("[RX]", 0,))
    thread.start_new_thread(getnode_details, ())
    thread.start_new_thread(poll_smartplugs, ())
except:
    print("Error: unable to start thread")

sendpkt()
