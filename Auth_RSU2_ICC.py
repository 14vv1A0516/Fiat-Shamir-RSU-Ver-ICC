import socket   
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
    '''
    def inorderTraversal(self, node: Node) -> None:
        if node:
            self.inorderTraversal(node.left)
            print(node.value)
            self.inorderTraversal(node.right)
    '''
    def getAuthenticationPath(self, value: str, i_val) -> Dict[int, str]:
        path = {}
        
        def findNode(node: Node, depth: int, leaf_index: int) -> bool:
            nonlocal i_val
            if node is None:
                return False
            
            if node.left is None and node.right is None:
                # Check if this is the leaf node and matches the value we're looking for
                if leaf_index == i_val:
                    #print("\nFound leaf node with value:", value)
                    if i_val % 2 == 0:
                        #print("\n1 l depth : ", depth, "& Node : ", node.value)
                        path[str(depth)+"l"] = node.value
                    else:
                        #print("\n1 r depth : ", depth, "& Node : ", node.value)
                        path[str(depth)+"r"] = node.value
                    return True
                else:
                    return False
                
            else:
                if node.left and findNode(node.left, depth + 1, leaf_index * 2):
                    #print("2 r depth : ", depth, "& Node : ", node.right.value)
                    path[str(depth)+"r"] = node.right.value
                    return True
                elif node.right and findNode(node.right, depth + 1, leaf_index * 2 + 1):
                    path[str(depth)+"l"] = node.left.value
                    #print("2 l depth : ", depth, "& Node : ", node.left.value)
                    return True
                return False 

        findNode(self.root, 0, 0)
        path[str(len(path))+ "z"] = self.root.value  # Add the root hash at the end of the path with the maximum depth
        #print("\n3 depth : ", len(path), "& Node : ", self.root.value,"\n")

        return path
    
    def getAncestorslist(self, value: str) -> List[str]:
        path = []
        def findNode(node: Node, value: str) -> bool:
            if node is None:
                return False
            elif node.value == value:
                # path.append(node.value)
                return True
            else:
                if node.left and findNode(node.left, value):
                    path.append(node.left.value)
                    return True
                elif node.right and findNode(node.right, value):
                    path.append(node.right.value)
                    return True
                return False
        findNode(self.root, value)
        path.append(self.root.value)
        return path
    
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

w_i = [1, 7, 15, 3, 4, 11, 9, 12, 16, 10, 2, 14, 13, 6, 8, 5]  # w^i till N = 16, D domain
w_2i = [1, 15, 4, 9, 16, 2, 13, 8]    

reg_sheet1 = pe.get_sheet (file_name= "RSU_Reg_ICC.xlsx")
auth_sheet2 = pe.get_sheet (file_name= "RSU_Auth2_ICC.xlsx")

# Create a TCP/IP socket
SDNC_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the server's address and port
server_address = ('10.13.4.78', 9912)
SDNC_socket.connect(server_address)
print(f"Connected to {server_address}\n****************************************") 

RSU_ID = "X40VR4E"
reg_flag = 0

for row in reg_sheet1 : # Get ( VID, PID, VPID, NVID, f(w^i), fe(w^2i), fo(w^2i), Veh_Reg_comp_time )
    if row[0] == RSU_ID :
        RPR = row[3]
        fx_list = row[4]
        
        f_w_i_root_hash = row[5]
        f_star_w_2i_root_hash = row[6]
        f_w_i = [int(i) for i in row[7].split(',')]
        f_star_w_2i = [int(i) for i in row[8].split(',')]
        reg_flag = 1 
        print ("  RSU_ID : ", RSU_ID, "match found ...")
        break

# print ("f_w_i : ", f_w_i)
# print ("f_star_w_2i : ", f_star_w_2i)

if reg_flag == 1 :
    print ("Reg flag found in Excel sheet")

    f_w_i_root_hash, f_w_i_mtree_obj = mixmerkletree (f_w_i)
    f_star_w_2i_root_hash, f_star_w_2i_mtree_obj = mixmerkletree (f_star_w_2i)

    while True : 
        print ("==========================\n")
        SDNC_ID_pub_inp_Auth_token_T1 = SDNC_socket.recv(1024).decode()  

        start1_comp_time = time.time ()
        SDNC_ID_pub_inp_Auth_token_T1 = [i for i in SDNC_ID_pub_inp_Auth_token_T1.split('&')]

        SDNC_ID = SDNC_ID_pub_inp_Auth_token_T1[0]
        SDNC_pub_inp = SDNC_ID_pub_inp_Auth_token_T1[1]
        Auth_token = SDNC_ID_pub_inp_Auth_token_T1[2]
        T1 = float (SDNC_ID_pub_inp_Auth_token_T1[3])

        if get_timestamp () - T1 < 4 :
            print ("T1 check Success ...")

            i_val_hash = hashlib.sha256(RSU_ID.encode('utf-8') + SDNC_pub_inp.encode('utf-8')).hexdigest()
            # print ("i_val_hash : ", i_val_hash)

            i_val = int(int(i_val_hash, 16) % (N/2 - 1))
            # print ("i_val int : ", i_val)

            ti = int(i_val_hash, 16) % 2

            get_f_w_i_val = f_w_i[i_val]
            get_f_w_N2_i = f_w_i[int(floor(N / 2)) + i_val]
            get_f_star_w_2i = f_star_w_2i[i_val]

            print ("Computed Challenge \nti = ", ti, "\ni_val = ", i_val)

            ABC_proof = [get_f_w_i_val, get_f_w_N2_i, get_f_star_w_2i]
            ABC_proof = listToString(ABC_proof)

            if ti == 0 :
                auth_path_for_ti = f_w_i_mtree_obj.getAuthenticationPath(Node.hash(str(f_w_i[i_val])), i_val)

            elif ti == 1 :
                auth_path_for_ti = f_star_w_2i_mtree_obj.getAuthenticationPath(Node.hash(str(f_star_w_2i[i_val])), i_val)

            #print ("auth_path_for_ti : ", auth_path_for_ti, type(auth_path_for_ti))

            auth_path_for_ti = str(auth_path_for_ti)
            #print ("\n----------------\nauth_path_for_ti : ", auth_path_for_ti, type(auth_path_for_ti))
            T2 = str(get_timestamp())
            RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2 = RSU_ID+ "&"+ RPR + "&"+ Auth_token + "&"+ ABC_proof + "&"+ auth_path_for_ti + "&"+ T2

            end1_comp_time = time.time ()

            SDNC_socket.send (RSU_ID_RPR_Auth_token_ABC_proof_auth_path_ti_T2.encode('utf')) 

            print ("Sending Response to Challenge to SDNC....")
            Auth_status = SDNC_socket.recv(1024).decode() 

            if Auth_status == "S" :

                print ("RSU Auth SUccesss ...")
                comp_time = end1_comp_time - start1_comp_time

                auth_sheet2.row += [ RSU_ID, comp_time ]
                auth_sheet2.save_as ("RSU_Auth2_ICC.xlsx")
                print ("RSU Auth Comp Time : ", comp_time)
            else :
                print ("RSU AUth Falied ...") 

        else :
            print ("RPR_star check failed")
else :
    print ("Reg flag not found")

