import socket   
import random # import randint
import time, datetime
from hashlib import sha256
import hashlib, threading 
import pyexcel as pe  
from math import floor

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

def handle_client(RSU_conn) :
    reg_sheet1 = pe.get_sheet (file_name= "SDNC_Reg_ICC.xlsx")

    print ("CLient connnnected -------------")
    SDNC_start_latency = time.time ()
    start1_comp_time = time.time ()

    SDNC_pub_inp = str(random.randint(100, 100000))
    Reg_token = str(random.randint(100, 100000))
    T1 = str(get_timestamp ())

    SDNC_ID_pub_inp_token_T1 = SDNC_ID + "&"+ SDNC_pub_inp + "&"+ Reg_token + "&"+ T1
    end1_comp_time = time.time()
    SDNC_comp_time = end1_comp_time - start1_comp_time

    RSU_conn.send (SDNC_ID_pub_inp_token_T1.encode('utf')) 

    RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2 = RSU_conn.recv(1024).decode('utf')  # Send (Auth_Req_f_wi) from Veh

    RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2 = [i for i in RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2.split('&')]

    RSU_ID = RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2[0]
    RPR = RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2[1]
    Reg_token_star = RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2[2]
    f_w_i_root_hash = RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2[3]
    f_star_root_hash = RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2[4]
    T2 = RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2[5]
    start2_comp_time = time.time ()
    # --------------------------------------
    if get_timestamp() - float(T2) < 4 and Reg_token == Reg_token_star:
        alpha = hashlib.sha256(RSU_ID.encode('utf-8') + SDNC_pub_inp.encode('utf-8')).hexdigest()
        alpha_int = int(alpha, 16) % N

        print ("*********** alpha int : ", alpha_int)

        end2_comp_time = time.time ()
        SDNC_comp_time += end2_comp_time - start2_comp_time 

        SDNC_end_latency = time.time ()
        Reg_latency = SDNC_end_latency - SDNC_start_latency
        reg_sheet1.row += [ RSU_ID, RPR, SDNC_pub_inp, f_w_i_root_hash, f_star_root_hash, alpha_int, SDNC_comp_time, Reg_latency ]
        reg_sheet1.save_as ("SDNC_Reg_ICC.xlsx")

        print ("\nSDNC_comp_time : ", SDNC_comp_time)
        print ("\nreg_latency : ", Reg_latency)

        print ("Successful RSU Registration ...")


        print ("\nReg Done SUCCESS \n ========================================")
    else :
            print ("Reg_Token match or T2 check Failed")
    
    RSU_conn.close ()

prime_field = 17 # w= 7 (generator), F_p field
w = 7
N = 16
ID_size = 7


SDNC_ID = "SDNC1"
host = "10.13.4.78" # socket.gethostname()
print("Host IP is ", host, "\nWaiting for Connection ....")
port = 6002  # initiate port no above 1024
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # get instance
server_socket.bind((host, port))  # bind host address and port together

server_socket.listen(40)
i = 0 

while True :
    client_socket, client_address = server_socket.accept()
    i = i + 1
    client_thread = threading.Thread (target=handle_client, args= (client_socket,))
    client_thread.start()
