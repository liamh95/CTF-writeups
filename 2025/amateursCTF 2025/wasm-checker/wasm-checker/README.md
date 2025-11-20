# wasm checker (Rev - 50)

> its a flag checker

---
## What we're given
We're given two files (plus a Dockerfile, but we don't really care about that): a Javascript file `main.mjs` and a web-assembly file, `module.wasm`.
The Javascript file does the following.

1. Prompts us for the flag.
2. Loads our response into memory.
3. Loads the function `check()` from `module.wasm`.
4. Checks our input using `check()`.

Presumably, the flag is the only input that makes `check()` happy.
The web-assembly file is essentially a compiled binary, so we can't really read it.
This will be my first itme encountering, let alone disassembling web-assembly.




---
## Disassembly - Ghidra

This is my first time encountering web-assembly and apparently [wabt](https://github.com/WebAssembly/wabt) and its `wasm2c` command are good for turning a `.wasm` file into a somewhat-readable `.c` (and accompanying `.h`) file.
I tried this and the resulting `.c` file had a lot of low-level stuff in it that I don't think was really important.
Luckilly, there's a [Ghidra extension](https://github.com/nneonneo/ghidra-wasm-plugin) that disassembles `.wasm` and shows `C` code that would compile to the same thing.

The `C` code Ghidra generates for the `check()` function is made up of a gorillion lines that look like this.
```C
undefined4 export::check(void)
{
    if (((((uint)DAT_ram_00000006 + (uint)DAT_ram_00000026) - (uint)DAT_ram_0000001f) -
       ((uint)bRam00000003 &
        (uint)(DAT_ram_00000015 ^ DAT_ram_00000029) -
        (uint)(DAT_ram_0000000c | DAT_ram_0000000d) * (uint)DAT_ram_0000001a |
       (uint)bRam00000002 | (uint)DAT_ram_00000023 + (uint)DAT_ram_00000027) |
      (uint)DAT_ram_00000014 - ((uint)DAT_ram_00000004 - (uint)DAT_ram_0000001e)) != 0x6e) {
        return 0;
    }
    if ((DAT_ram_0000000a | DAT_ram_00000024) != 0x5f) {
        return 0;
    }
    if (((DAT_ram_0000001b ^ DAT_ram_00000008) & DAT_ram_0000000f) != 0x2d) {
        return 0;
    }
    ...

```
The `DAT_ram_XXXXXXXX` bytes come from the flag, read sequentially into memory, but the actual `check()` function looks obfuscated.
Each part of the check performs some arithmetic and/or bitwise operations on some of the bytes and compares the result to some value, so finding the flag amounts to finding a sequence of bytes that satisfies a bunch of equations.


---
## Solving equations with Z3
This is why God created [Z3](https://ericpony.github.io/z3py-tutorial/guide-examples.htm).
Looking through the `C` code we see that the flag should have `0x30` bytes, so we just set up that many variables in Z3 and copy all of the checks over as equations.

```Python
from z3 import *

s = Solver()

flag = [BitVec('flag[%s]' % i, 8) for i in range(0x30)]

equations = [
( ( (flag[6] + flag[0x26]) - flag[0x1f]) -(flag[3] & (flag[0x15] ^ flag[0x29]) - (flag[0x0c] | flag[0x0d]) * flag[0x1a] | flag[2] | flag[0x23] + flag[0x27]) | flag[0x14] - (flag[0x04] - flag[0x1e])) == 0x6e,
...
]

for eq in equations:
	s.add(eq)

if s.check() == sat:
	m = s.model()
	for var in flag:
		print(f'{var} = {m[var]}')
	print(''.join([chr(m[var].as_long()) for var in flag[:43]]))
else:
	print('No solution :(')
```

Thankfully, we have a solution.

---

## Conclusion
1. Ghidra can deal with `.wasm` too.
2. Z3 is dank.