from pwn import *

conn = remote("ctf.2600.eu", 7778)
question = conn.recvline().decode().strip()
print("Question:", question)

tokens = question.split()
a_bin = tokens[-4]
op = tokens[-3]
b_bin = tokens[-2]

a_int = int(a_bin, 2)
b_int = int(b_bin, 2)

if op == "XOR":
    result_int = a_int ^ b_int
elif op == "AND":
    result_int = a_int & b_int
elif op == "OR":
    result_int = a_int | b_int
else:
    raise ValueError("Opérateur inconnu :", op)

result_bin = bin(result_int)[2:]

conn.sendline(result_bin.encode())


conn.interactive()