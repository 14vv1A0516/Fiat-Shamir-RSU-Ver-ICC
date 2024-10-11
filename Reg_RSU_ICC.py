import socket  
import string     
import random # import randint
import time, datetime 
from hashlib import sha256 
import hashlib 
import pyexcel as pe  
from math import floor 
from typing import List, Dict 

class Node: 
    def __init__(self, left, right, value: str, content, is_copied=False) -> None:
        self.left: Node = left
        self.right: Node = right
        self.value = value
        self.content = content
        self.is_copied = is_copied
         
    @staticmethod
    def hash(val: str) -> str:
        return hashlib.sha256(val.encode('utf-8')).hexdigest()
 
    def __str__(self):
        return (str(self.value))
 
    def copy(self):
        """
        class copy function
        """
        return Node(self.left, self.right, self.value, self.content, True)
       
class MerkleTree:
    def __init__(self, values: List[str]) -> None:
        self.__buildTree(values)
 
    def __buildTree(self, values: List[str]) -> None:
 
        leaves: List[Node] = [Node(None, None, Node.hash(str(e)), str(e)) for e in values]
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1].copy())  # duplicate last elem if odd number of elements
        self.root: Node = self.__buildTreeRec(leaves)
 
    def __buildTreeRec(self, nodes: List[Node]) -> Node:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1].copy())  # duplicate last elem if odd number of elements
        half: int = len(nodes) // 2
 
        if len(nodes) == 2:
            return Node(nodes[0], nodes[1], Node.hash(nodes[0].value + nodes[1].value), nodes[0].content+"+"+nodes[1].content)
 
        left: Node = self.__buildTreeRec(nodes[:half])
        right: Node = self.__buildTreeRec(nodes[half:])
        value: str = Node.hash(left.value + right.value)
        content: str = f'{left.content}+{right.content}'
        return Node(left, right, value, content)
 
    def printTree(self) -> None:
        self.__printTreeRec(self.root)
         
    def __printTreeRec(self, node: Node) -> None:
        if node != None:
            if node.left != None:
                print("Left: "+str(node.left))
                print("Right: "+str(node.right))
            else:
                print("Input")
                 
            if node.is_copied:
                print('(Padding)')
            print("Value: "+str(node.value))
            print("Content: "+str(node.content))
            print("")
            self.__printTreeRec(node.left)
            self.__printTreeRec(node.right)
 
    def getRootHash(self) -> str: 
        return self.root.value
    
def mixmerkletree(f_w_i) -> None:
    #print("Inputs: ")
    #print(*f_w_i, sep=" | ")
    #print("")
    mtree = MerkleTree(f_w_i)
    print("Root Hash: "+ mtree.getRootHash()+"\n")
    #mtree.printTree()
    #print("\nInorder Traversal:\n")
    #mtree.inorderTraversal(mtree.root)
    return mtree.getRootHash(), mtree

def printPoly(poly, n):
    # Initialize an empty string to store the polynomial
    polynomial_str = ""

    for i in range(n):
        # Append the coefficient and x term to the string
        if poly[i] != 0:
            polynomial_str += str(poly[i]) + "x^" + str(i) + " + "

    # Remove the trailing " + " from the end of the string
    polynomial_str = polynomial_str[:-3]

    # Print the entire polynomial in a single line
    print(polynomial_str)

def evaluate_polynomial(coefficients, x):
    result = 0
    for i, coef in enumerate(coefficients):
        result += coef * (x ** (len(coefficients) - 1 - i))
    return result

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

prime_field = 17            # w= 7 (generator), F_p field
w = 7
N = 16
ID_size = 7


w_i = [1, 7, 15, 3, 4, 11, 9, 12, 16, 10, 2, 14, 13, 6, 8, 5]  # w^i till N = 16, D domain
w_2i = [1, 15, 4, 9, 16, 2, 13, 8]   # w^2i till N = 8, D* domain

reg_sheet1 = pe.get_sheet (file_name= "RSU_Reg_ICC.xlsx")

RSU_ID = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(ID_size))
RSU_PIN = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(ID_size))

print ("RSU_ID : ", RSU_ID)
# Create a TCP/IP socket
SDNC_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the server's address and port
SDNC_address = ('10.13.4.78', 6002)
SDNC_socket.connect(SDNC_address)
print(f"Connected to {SDNC_address}\n****************************************") 

SDNC_ID_pub_inp_token_T1 = SDNC_socket.recv(1024).decode('utf') 

start_comp_time = time.time ()
RSU_r = random.randint(100, 100000)

RPR = hashlib.sha256(RSU_ID.encode('utf-8') + RSU_PIN.encode('utf-8') + str(RSU_r).encode('utf-8')).hexdigest()

#print("Polynomial f(x)= ")
fx_list = []

f_deg = random.randint(6, 12)

for i in range(0, f_deg + 1):
    fx_list.append(random.randint(-100, 100))

# fx_list = [2, 5, 10, 6, 7, 9, 4, 14]

f_len = len(fx_list)
#print ("f list from lowest degree term  is ", f_list)  # [a_n, a_{n-1}, ..., a_1, a_0]
# printPoly(fx_list, f_len)
fx_list.reverse ()

print ("Poly f list highest degree term is ", fx_list) # [a_0, a_1, ..., a_{n-1}, a_n]

f_w_i = []

for each in w_i :
    result = evaluate_polynomial(fx_list, each) # f_list : [a_n, a_{n-1}, ..., a_1, a_0]
    f_w_i.append(result % prime_field)  

#print(f"The result of evaluating the polynomial at x = {each} is: {result}")
# print("Subgroup D(w^i): ", w_i)
# print ("f_w_i : ", f_w_i)

f_w_i_str = [str(num) for num in f_w_i]
f_w_i_root_hash, f_w_i_mtree_obj = mixmerkletree (f_w_i_str)

# print ("f_w_i is ", f_w_i)

f_star_w_2i = []
f_star_len = floor(N/2) # - 1

fo_list = []
fe_list = []

# print ("fx_list : ", fx_list)
deg = len(fx_list)
i = 0

if deg % 2 == 0: # fx is odd degree
    while i < len(fx_list)-2:
        fo_list.append(fx_list[i])
        i = i + 1
        fe_list.append(fx_list[i])
        i = i + 1
    if i == len(fx_list)-2 :
        fo_list.append(fx_list[i])
        i = i + 1
        fe_list.append(fx_list[i])
        
elif deg % 2 != 0: # fx is even degree
    while i < len(fx_list)-2:
        fe_list.append(fx_list[i])
        i = i + 1
        if i == len(fx_list)-2 :
            fo_list.append(fx_list[i])
            i = i + 1
            fe_list.append(fx_list[i])
        else:
            fo_list.append(fx_list[i])
            i = i + 1

# print ("fe(x) : ", fe_list)
# print ("fo(x) : ", fo_list)

fe_w_2i = [] 
fo_w_2i = []

for each in w_2i :
    result = evaluate_polynomial(fe_list, each) # f_list : [a_n, a_{n-1}, ..., a_1, a_0]
    fe_w_2i.append(result % prime_field)  

for each in w_2i :
    result = evaluate_polynomial(fo_list, each) # f_list : [a_n, a_{n-1}, ..., a_1, a_0]
    fo_w_2i.append(result % prime_field)

# print ("fe_w_2i : ", fe_w_2i)
# print ("fo_w_2i : ", fo_w_2i)


SDNC_ID_pub_inp_token_T1 = [i for i in SDNC_ID_pub_inp_token_T1.split('&')]

SDNC_ID = SDNC_ID_pub_inp_token_T1[0]
SDNC_pub_inp = SDNC_ID_pub_inp_token_T1[1]
Reg_token = SDNC_ID_pub_inp_token_T1[2]
T1 = float(SDNC_ID_pub_inp_token_T1[3])

if get_timestamp() - T1 < 4 :

    alpha = hashlib.sha256(RSU_ID.encode('utf-8') + SDNC_pub_inp.encode('utf-8')).hexdigest()
    alpha_int = int(alpha, 16) % N

    print ("******** alpha int : ", alpha_int) 

    for i in range(f_star_len) :
        f_star_w_2i.append( (fe_w_2i[i] + alpha_int * fo_w_2i[i]) % prime_field ) 
    
    print ("f_star_w_2i : ", f_star_w_2i)

    f_star_w_2i_root_hash, f_star_w_2i_mtree_obj = mixmerkletree (f_star_w_2i)

    T2 = get_timestamp ()

    RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2 = RSU_ID + "&"+ RPR + "&"+ Reg_token + "&"+ f_w_i_root_hash + "&"+ f_star_w_2i_root_hash + "&"+ str(T2)

    end_comp_time = time.time ()
    RSU_Comp_time = end_comp_time - start_comp_time

    # print ("RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2 : ", RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2)
    SDNC_socket.send (RSU_ID_RPR_Reg_token_f_f_star_root_hash_T2.encode('utf'))
    
    print ("\nReg Done SUccess for RSU")

    reg_sheet1.row += [ RSU_ID, RSU_PIN, RSU_r, RPR, listToString(fx_list), f_w_i_root_hash, f_star_w_2i_root_hash, listToString(f_w_i), listToString(f_star_w_2i), SDNC_pub_inp, Reg_token, RSU_Comp_time ]
    reg_sheet1.save_as ("RSU_Reg_ICC.xlsx")

    print ("RSU Comp Time for ZKP Reg of RSU ", RSU_ID, " is ", RSU_Comp_time, "\n")

else :
    print ("Reg Failed ")
