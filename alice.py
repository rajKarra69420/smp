from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import time, socket, pickle, os, sys

from encrypt_decrypt import encrypt, decrypt
from cryptography.hazmat.primitives import serialization

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65433        # The port used by the server
alice_priv = ec.generate_private_key(ec.SECP384R1())

digest = hashes.Hash(hashes.SHA256())
#read in file contents
#filename is input arg on command line
filename = sys.argv[1]
fileContents = open(filename, 'rb')
fileStuff = fileContents.read()
digest.update(fileStuff)
fileHash = digest.finalize()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    s.connect((HOST, PORT)) #Connect to the socket

    #serialize key
    serialKey = alice_priv.public_key().public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo)
    s.sendall(serialKey) #Send over alice's public key
    bob_public = s.recv(1024)
    #deserialize key
    loaded_public_key = serialization.load_pem_public_key(bob_public)
    alice_shared = alice_priv.exchange(ec.ECDH(), loaded_public_key)
    alice_hkdf = HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'',).derive(alice_shared)
    #Now we can encrypt alice's message and send it over
    # time.sleep(5)
    iv, ciphertext, tag = encrypt(alice_hkdf,fileHash,b"lol")
    myCiphertext = ciphertext
    s.sendall(pickle.dumps((iv,ciphertext,tag)))
    (iv, ciphertext, tag) = pickle.loads(s.recv(102400))
    results = decrypt(alice_hkdf, b"lol", iv, ciphertext,tag)
    if results == fileHash:
        print("Success!")
    else:
        print("Failed!")
        print(results)
        print(fileStuff)


