from pwn import *

r = remote('crypto.chal.csaw.io', 1578)

flag = ''
found = ''

r.recv()
while found != '}':
	if len(flag) < 16:
		sendme = 'A'*(15-len(flag))
	else:
		sendme = 'A'*(15-(len(flag)%16))
	r.sendline(sendme)
	if len(flag) < 16:
		matchme = r.recvline()[16:48]
	else:
		matchme = r.recvline()[48:80]
	for i in range(32, 127): #only need to check printable characters
		prompt = r.recv()
		r.sendline(sendme + flag + chr(i))
		response = r.recvline()
		if len(flag) < 16 and response[16:48] == matchme:
			flag += chr(i)
			found = chr(i)
			break
		elif len(flag) >= 16 and response[48:80] == matchme:
			flag += chr(i)
			found = chr(i)
			break
	print flag
	r.recv()
