import socket  
import random # import randint
import time, datetime 
from hashlib import sha256  
import hashlib 
import pyexcel as pe  
from math import floor

import threading  
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset  # Import dpset here
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

def Ver_merkle_path(auth_path, root_hash):
    skip_count = 0

    for key, value in auth_path.items():
        #print(f"Key: {key}, Value: {value}")

        if skip_count >= 3:
            #print ("Into If part ****")
            
            if key[1] == "l" :
                prev_hash = sha256(auth_path[key].encode('utf-8') + prev_hash.encode('utf-8')).hexdigest()
                #print ("11 Prev hash is ", prev_hash)

            elif key[1] == "r" :
                prev_hash = sha256(prev_hash.encode('utf-8') + auth_path[key].encode('utf-8')).hexdigest()
                #print ("22 Prev hash is ", prev_hash)

        else:
            #print ("Into else ---")
            if key[1] == "l" :
                value1 = auth_path[key]
            elif key[1] == "r" :
                value2 = auth_path[key]

            skip_count += 1

            if skip_count == 2 :
                prev_hash = sha256(value1.encode('utf-8') + value2.encode('utf-8')).hexdigest()
                #print ("33 Prev hash is ", prev_hash)
                skip_count += 1

    if prev_hash == root_hash :
        return 1
    else :
        return 0

def listToString(s): 
    # initialize an empty string
    str1 = ""
 
    # traverse in the string
    for ele in s:
        str1 += str(ele)
        str1 += ","
    str1 = str1[:len(str1)-1]
    return str1

def get_timestamp() :
    ct = datetime.datetime.now()
    ts = ct.timestamp()
    return ts

class SimpleSwitch13(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}  # Add this line to initialize dpset

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.dpset = kwargs['dpset']  # Get the dpset from the context

        self.prime_field = 17            # w= 7 (generator), F_p field
        self.w = 7
        self.N = 16
        self.SDNC_ID = "SDNC1"

        # Start the TCP servers to receive metrics from RSUs
        # SDNC21_conn_thread = threading.Thread(target=self.start_SDNC21_conn, args=("127.0.0.1", 9210 ))

        server_thread_1 = threading.Thread(target=self.start_RSU1_server, args=("10.13.4.78", 9911, "RSU1"))
        server_thread_2 = threading.Thread(target=self.start_RSU2_server, args=("10.13.4.78", 9912, "RSU2"))

        server_thread_1.start()
        server_thread_2.start()

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, hard_timeout=0):
        # Prepare the OpenFlow protocol parser and ofproto
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Set the flow instructions to apply the actions
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        # Construct a FlowMod message to add a flow
        if buffer_id:
            # print ("Into Iffffff of addFlow")
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, priority=priority, match=match,
                                    instructions=inst, hard_timeout=hard_timeout)
        else:
            # print ("Into Elssssssse of addFlow")
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match,
                                    instructions=inst, hard_timeout=hard_timeout)

        # Send the flow mod message to the switch
        datapath.send_msg(mod)

    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # Learn a MAC address to avoid flooding next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def start_RSU1_server(self, host, port, rsu_name):
        """Start a TCP server to receive metrics from an RSU."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"{rsu_name} Server started on {host}:{port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connection established with {addr} for {rsu_name}")
            threading.Thread(target=self.handle_RSU1, args=(conn, )).start()

    def start_RSU2_server(self, host, port, rsu_name):
        """Start a TCP server to receive metrics from an RSU."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"{rsu_name} Server started on {host}:{port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connection established with {addr} for {rsu_name}")
            threading.Thread(target=self.handle_RSU2, args=(conn, )).start() 


    def handle_RSU1(self, RSU1_conn) :
        reg_sheet1 = pe.get_sheet (file_name= "SDNC_Reg_ICC.xlsx")
        auth_sheet1 = pe.get_sheet (file_name= "SDNC_auth1_ICC.xlsx")
        reg_flag = 0

        RSU_ID = "NT0P1GR"
        for row in reg_sheet1 : 
            if row[0] == RSU_ID :
                RPR = row[1]
                SDNC_pub_inp = row[2]
                f_w_i_root_hash = row[3]
                f_star_w_2i_root_hash = row[4]
                alpha = row[5]
                
                reg_flag = 1 
                print ("  RSU_ID : ", RSU_ID, "match found ...")
                break

        print ("RPR : ", RPR)
        print ("***** alpha : ", alpha)

        if reg_flag == 1 :
            print ("Reg Flag found in Excel sheet -------------")
            while True : 
                print ("====================================\n")
                time.sleep (5)
                start_latency = time.time ()
                start1_comp_time = time.time ()

                SDNC_pub_inp = str(random.randint(100, 100000))
                Auth_token = random.randint(100, 100000)

                # i_val = random.randint(0, floor(N/2)-1)
                # ti = random.randint(0, 1)
                T1 = get_timestamp ()

                SDNC_ID_pub_inp_Auth_token_T1 = self.SDNC_ID+ "&"+ str(SDNC_pub_inp) + "&"+ str(Auth_token) + "&"+ str(T1)

                end1_comp_time = time.time ()

                auth_comp_time = end1_comp_time - start1_comp_time

                RSU1_conn.send (SDNC_ID_pub_inp_Auth_token_T1.encode('utf')) 
                RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2 = RSU1_conn.recv (1024).decode('utf') # Recv ( ABC_proof )

                RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2 = [i for i in RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2.split('&')]

                RSU_ID = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[0]
                RPR_star = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[1]
                Auth_token_star = int(RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[2])
                ABC = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[3]
                Authpath_ti = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[4]
                T2 = float(RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[5])

                #  print (" Time diff : ", get_timestamp() - T2)
                if get_timestamp() - T2 < 4 and Auth_token == Auth_token_star and RPR == RPR_star:
                    print ("Proof Received from RSU 11111, ") #, RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2," \nVerifying Proof ....") #is ", ABC_authpath_rA)

                    i_val_hash = hashlib.sha256(RSU_ID.encode('utf-8') + SDNC_pub_inp.encode('utf-8')).hexdigest()

                    # print ("i_val_hash : ", i_val_hash)
                    i_val = int(int(i_val_hash, 16) % (self.N/2 - 1))
                    ti = int(i_val_hash, 16) % 2

                    print ("i_val int : ", i_val)
                    
                    start2_comp_time = time.time ()
                    Authpath_ti = eval(Authpath_ti)

                    if ti == 0 :
                        #print ("\nVer merkle path for f(w^i) ")
                        merkle_ver_status = Ver_merkle_path (Authpath_ti, f_w_i_root_hash )
                    elif ti == 1 :
                        #print ("\nVer merkle path for fstar(w^2i) ")
                        merkle_ver_status = Ver_merkle_path (Authpath_ti, f_star_w_2i_root_hash )

                    #print ("\nMerkle Status is ", merkle_ver_status)

                    if merkle_ver_status == 1 :
                        print ("---------Merkle  path Verified SUCCESSFUL 1111 ---------")

                        ABC_proof_list = [int(i) for i in ABC.split(',')] # Y1, Y2, Y3 values

                        #print ("Received ABC Y-coordinates are ", ABC_proof_list)

                        # Example usage:
                        x_values = [ (self.w**i_val) % self.prime_field, (self.w**(floor(self.N/2)+ i_val)) % self.prime_field] #, alpha 
                        y_values = [ ABC_proof_list[0] , ABC_proof_list[1] ] # , ABC_proof_list[2]
                        #alpha = int(alpha)

                        print ("A : (", x_values[0], ",", y_values[0], ")")
                        print ("B : (", x_values[1], ",", y_values[1], ")")

                        
                        w_minus_i_mod_p = pow(self.w, -i_val, self.prime_field)
                        inv_2_mod_p = pow(2, -1, self.prime_field)

                        term1 = 1 + alpha * w_minus_i_mod_p 
                        term2 = 1 - alpha * w_minus_i_mod_p

                        y3_for_alpha = ((term1 *  y_values[0] + term2 * y_values[1] ) * inv_2_mod_p) % self.prime_field
                        print ("\nComputed C : (", alpha, ",", y3_for_alpha, ")")

                        #print(f"The result of Lagrange interpolation at x = {x_to_evaluate} is: {y3_for_alpha}")

                        if y3_for_alpha == ABC_proof_list[2]:
                            print ("---- Lagrange interpolation Ver SUCCESSFUL 1111-----------")
                            Auth_status = "S"
                            end2_comp_time = time.time ()

                            RSU1_conn.send (Auth_status.encode('utf')) 
                            print ("******Authentication SUCCESS *****")
                                
                        else :
                            Auth_status = "F"
                            RSU1_conn.send (Auth_status.encode('utf')) 
                            print ("Lagrange interpolation Failed")
                    else :
                        print ("Merkle Auth failed ")

                    #print ("Received f_star_w_2i_root_hash: ", f_star_w_2i_root_hash)

                    auth_comp_time += end2_comp_time - start2_comp_time

                    end_latency = time.time ()
                    total_latency = end_latency - start_latency
                            
                    auth_sheet1.row += [ RSU_ID, auth_comp_time, total_latency ]
                    auth_sheet1.save_as ("SDNC_auth1_ICC.xlsx")

                    print ("Fog Auth comp time is ", auth_comp_time)
                    print ("Total latency is ", total_latency,"\n\n*******************************")

                else :
                    print ("T2 check failed ...")
        else :
            print ("Reg Details Not found ...")

        RSU1_conn.close ()

    def handle_RSU2(self, RSU2_conn) :
        reg_sheet1 = pe.get_sheet (file_name= "SDNC_Reg_ICC.xlsx")
        auth_sheet2 = pe.get_sheet (file_name= "SDNC_auth2_ICC.xlsx")
        reg_flag = 0

        RSU_ID = "X40VR4E"
        for row in reg_sheet1 : 
            if row[0] == RSU_ID :
                RPR = row[1]
                SDNC_pub_inp = row[2]
                f_w_i_root_hash = row[3]
                f_star_w_2i_root_hash = row[4]
                alpha = row[5]
                
                reg_flag = 1 
                print ("  RSU_ID : ", RSU_ID, "match found ...")
                break

        # print ("RPR : ", RPR)
        print ("***** alpha : ", alpha)

        if reg_flag == 1 :
            print ("Reg Flag found in Excel sheet -------------")

            while True : 
                print ("====================================\n")
                time.sleep (5)
                start_latency = time.time ()
                start1_comp_time = time.time ()

                SDNC_pub_inp = str(random.randint(100, 100000))
                Auth_token = random.randint(100, 100000)

                # i_val = random.randint(0, floor(N/2)-1)
                # ti = random.randint(0, 1)
                T1 = get_timestamp ()

                SDNC_ID_pub_inp_Auth_token_T1 = self.SDNC_ID+ "&"+ str(SDNC_pub_inp) + "&"+ str(Auth_token) + "&"+ str(T1)

                end1_comp_time = time.time ()

                auth_comp_time = end1_comp_time - start1_comp_time

                RSU2_conn.send (SDNC_ID_pub_inp_Auth_token_T1.encode('utf')) 
                RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2 = RSU2_conn.recv (1024).decode('utf') # Recv ( ABC_proof )

                RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2 = [i for i in RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2.split('&')]

                RSU_ID = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[0]
                RPR_star = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[1]
                Auth_token_star = int(RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[2])
                ABC = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[3]
                Authpath_ti = RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[4]
                T2 = float(RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2[5])

                # print ("Auth_token : ", Auth_token, type(Auth_token))
                # print ("Auth_token_star : ", Auth_token_star, type(Auth_token_star))

                # print ("RPR : ", RPR, type(RPR))
                # print ("RPR_star : ", RPR_star,  type(RPR_star))

                
                if get_timestamp() - T2 < 4 and Auth_token == Auth_token_star and RPR == RPR_star:
                    print ("Proof Received from RSU 2222 ") #, RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2," \nVerifying Proof ....") #is ", ABC_authpath_rA)

                    i_val_hash = hashlib.sha256(RSU_ID.encode('utf-8') + SDNC_pub_inp.encode('utf-8')).hexdigest()

                    # print ("i_val_hash : ", i_val_hash)
                    i_val = int(int(i_val_hash, 16) % (self.N/2 - 1))
                    ti = int(i_val_hash, 16) % 2

                    print ("i_val int : ", i_val)
                    
                    start2_comp_time = time.time ()
                    Authpath_ti = eval(Authpath_ti)

                    if ti == 0 :
                        #print ("\nVer merkle path for f(w^i) ")
                        merkle_ver_status = Ver_merkle_path (Authpath_ti, f_w_i_root_hash )
                    elif ti == 1 :
                        #print ("\nVer merkle path for fstar(w^2i) ")
                        merkle_ver_status = Ver_merkle_path (Authpath_ti, f_star_w_2i_root_hash )

                    #print ("\nMerkle Status is ", merkle_ver_status)

                    if merkle_ver_status == 1 :
                        print ("---------Merkle  path Verified SUCCESSFUL 2222 ---------")

                        ABC_proof_list = [int(i) for i in ABC.split(',')] # Y1, Y2, Y3 values

                        #print ("Received ABC Y-coordinates are ", ABC_proof_list)

                        # Example usage:
                        x_values = [ (self.w**i_val) % self.prime_field, (self.w**(floor(self.N/2)+ i_val)) % self.prime_field] #, alpha 
                        y_values = [ ABC_proof_list[0] , ABC_proof_list[1] ] # , ABC_proof_list[2]
                        #alpha = int(alpha)

                        print ("A : (", x_values[0], ",", y_values[0], ")")
                        print ("B : (", x_values[1], ",", y_values[1], ")")

                        
                        w_minus_i_mod_p = pow(self.w, -i_val, self.prime_field)
                        inv_2_mod_p = pow(2, -1, self.prime_field)

                        term1 = 1 + alpha * w_minus_i_mod_p 
                        term2 = 1 - alpha * w_minus_i_mod_p

                        y3_for_alpha = ((term1 *  y_values[0] + term2 * y_values[1] ) * inv_2_mod_p) % self.prime_field
                        print ("\nComputed C : (", alpha, ",", y3_for_alpha, ")")

                        #print(f"The result of Lagrange interpolation at x = {x_to_evaluate} is: {y3_for_alpha}")

                        if y3_for_alpha == ABC_proof_list[2]:
                            print ("---- Lagrange interpolation Ver SUCCESSFUL 2222 -----------")
                            Auth_status = "S"
                            end2_comp_time = time.time ()
                            RSU2_conn.send (Auth_status.encode('utf')) 
                            print ("******Authentication SUCCESS *****")
                                
                        else :
                            Auth_status = "F"
                            RSU2_conn.send (Auth_status.encode('utf')) 
                            print ("Lagrange interpolation Failed")
                    else :
                        print ("Merkle Auth failed ")

                    #print ("Received f_star_w_2i_root_hash: ", f_star_w_2i_root_hash)
                    
                    auth_comp_time += end2_comp_time - start2_comp_time

                    end_latency = time.time ()
                    total_latency = end_latency - start_latency
                            
                    auth_sheet2.row += [ RSU_ID, auth_comp_time, total_latency ]
                    auth_sheet2.save_as ("SDNC_auth2_ICC.xlsx")

                    print ("Fog Auth comp time is ", auth_comp_time)
                    print ("Total latency is ", total_latency,"\n\n*******************************")

                else :
                    print ("T2 check failed ...")
        else :
            print ("Reg Details Not found ...")

        RSU2_conn.close ()

'''

host = "localhost" # socket.gethostname()
print("Host IP is ", host, "\nWaiting for Connection ....")
port = 6002  # initiate port no above 1024
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # get instance
server_socket.bind((host, port))  # bind host address and port together

server_socket.listen(40)
i =0 

while True :
    client_socket, client_address = server_socket.accept()
    i = i + 1
    client_thread = threading.Thread (target=handle_client, args= (client_socket,))
    client_thread.start()

'''
