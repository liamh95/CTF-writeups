from pwn import *
import subprocess

conn = remote('challs.umdctf.io', 30309)


conn.recvuntil(b'curl ')
pow_line = b'curl ' + conn.recvline().strip()
proof = subprocess.run(pow_line.decode(), shell=True, capture_output=True, text=True)

conn.sendline(proof.stdout.strip().encode())

print(conn.recvuntil(b'measure every input qubit as q[i] -> c[i]'))
print(conn.recvline())


conn.sendline(b'OPENQASM 2.0;')
conn.sendline(b'include "qelib1.inc";')
conn.sendline(b'qreg q[17];')
conn.sendline(b'creg c[16];')


# put ancilla into |-> for phase kickback
conn.sendline(b'x q[16];')
conn.sendline(b'h q[16];')

# prepare uniform superposition
for i in range(16):
    conn.sendline(b'h q[%d];' % i)

# do grover
oracle_line = b'oracle q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15],q[16];'
diffuse_line = b'diffuse q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15];'

for i in range(201):
    conn.sendline(oracle_line)
    conn.sendline(diffuse_line)

# measure
for i in range(16):
    conn.sendline(b'measure q[%d] -> c[%d];' % (i, i))

conn.sendline(b'END')

print(conn.recvall())