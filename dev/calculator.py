from pwn import *

conn = remote("ctf.2600.eu", 7777)
question = conn.recv(timeout=1).decode().strip()
print("question:",question)

expr = question.split("=")[0]

result = str(eval(expr))

print("resultat calculer:", result)

conn.sendline(result.encode())

conn.interactive()