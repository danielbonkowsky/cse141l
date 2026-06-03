"""
DelicateArch machine-code interpreter.

Loads an assembled `.mem` file (one 9-bit binary word per line, as emitted by
`assembler.py`) and executes it with a fetch-decode-execute loop on top of the
existing `Machine` model in `util.py`. This is the only way to *run* an assembled
program end-to-end (the Verilog DUT is WIP), so it is used to verify the hand
written `.asm` programs against their Python golden models.

Reuses every ALU/flag operation from `Machine` — the decoder only routes opcodes
to the right method; it never reimplements arithmetic or flag logic.

Usage (programmatic):
    from run_mem import run
    vm = run("program3/program3.mem", input_mem)   # input_mem: list[int] len 256
    product = vm.mem[64].uint

Usage (CLI, dumps non-zero memory after halt):
    python run_mem.py program1/program1.mem
"""

import sys
from pathlib import Path

from bitstring import BitArray
from util import Machine


# R/I opcodes (instr[7:4]) → Machine method name. None = handled specially.
_REG_OPS = {
    0x0: "and_R", 0x1: "xor_R", 0x3: "add_R", 0x4: "sub_R",
    0x5: "mov_R", 0x6: "sto_R", 0x7: "ld_R", 0x8: "st_R", 0x9: "cmp_R",
}

DONE_WORD = 0b100000000   # `done` / `beq 0`


def load_mem(path: str) -> list[int]:
    """Read a .mem file into a list of 9-bit instruction words."""
    rom: list[int] = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rom.append(int(line, 2))
    return rom


def run(mem_path: str, input_mem: list[int] | None = None,
        max_steps: int = 1_000_000) -> Machine:
    """Execute the program at `mem_path`; return the Machine after it halts.

    `input_mem` (if given) is a list of byte values written into data memory
    before execution. r0 is forced to 0 (hardwired in the real machine).
    """
    rom = load_mem(mem_path)
    vm = Machine()
    vm.reg0 = BitArray(uint=0, length=8)          # r0 hardwired to 0

    if input_mem is not None:
        for addr, val in enumerate(input_mem):
            vm.mem[addr] = BitArray(uint=val & 0xFF, length=8)

    pc = 0
    for _ in range(max_steps):
        if pc < 0 or pc >= len(rom):
            raise RuntimeError(f"PC {pc} out of ROM range [0,{len(rom)})")
        word = rom[pc]

        if word == DONE_WORD:
            return vm

        if word & 0b100000000:                    # B-type
            cond = (word >> 6) & 0b11
            off = word & 0x3F
            if off >= 32:
                off -= 64
            z = vm.zero_flag.uint
            s = vm.sign_flag.uint
            c = vm.carry_flag.uint
            v = vm.overflow_flag.uint
            taken = (
                (cond == 0b00 and z) or            # beq
                (cond == 0b01 and not z) or        # bne
                (cond == 0b10 and (s != v)) or     # blt
                (cond == 0b11 and c)               # bltu
            )
            pc = pc + off if taken else pc + 1
            continue

        # R/I-type
        op = (word >> 4) & 0xF
        field = word & 0xF
        if op in _REG_OPS:
            getattr(vm, _REG_OPS[op])(f"r{field}")
            pc += 1
        elif op == 0x2:                            # inv (field unused)
            vm.inv_R()
            pc += 1
        elif op == 0xA:                            # jmp rN — absolute
            pc = vm._get_reg(f"r{field}").uint
        elif op == 0xB:                            # shf imm (signed 4-bit)
            imm = field - 16 if field >= 8 else field
            vm.shf_I(BitArray(int=imm, length=8))
            pc += 1
        elif op == 0xC:                            # ldi imm (unsigned 4-bit)
            vm.ldi_I(BitArray(uint=field, length=8))
            pc += 1
        elif op == 0xD:                            # addi imm (signed 4-bit, sign-extended)
            imm = field - 16 if field >= 8 else field
            vm.addi_I(BitArray(uint=imm & 0xFF, length=8))
            pc += 1
        else:
            raise RuntimeError(f"Unknown opcode 0x{op:X} at PC {pc} (word {word:09b})")

    raise RuntimeError(f"Did not halt within {max_steps} steps (infinite loop?)")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_mem.py <program.mem>", file=sys.stderr)
        return 1
    vm = run(sys.argv[1])
    print("Non-zero data memory after halt:")
    for addr, b in enumerate(vm.mem):
        if b.uint:
            print(f"  mem[{addr:3}] = {b.uint:3} (0x{b.uint:02X})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
