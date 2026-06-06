# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CSE 141L course project: design and implement a custom 9-bit RISC processor called **DelicateArch**. The processor must run three programs: Hamming distance pairs (Program 1), arithmetic difference pairs (Program 2), and 16×16-bit multiplication (Program 3). The ISA is accumulator-based with separate instruction and data memory.

## Common Commands

**Assemble an `.asm` file to `.mem`:**
```sh
python assembler.py program1/program1.asm         # writes program1.mem
python assembler.py program1/program1.asm out.mem # custom output path
```

**Run Python program simulations / tests:**
```sh
python python_implementations/ham_pairs.py       # Program 1
python python_implementations/arith_pairs.py     # Program 2
python python_implementations/double_prec_mult.py # Program 3
```

**Simulate Verilog (Questa/ModelSim):**
```sh
# Run from verilog_code/ directory
vsim -do "vsim Top_tb; run -all"
vsim -do "vsim tb_alu; run -all"
```

The `.mem` output from the assembler is loaded by `InstROM.sv` via `$readmemb("mach_code.txt", Core)` — rename/copy to `mach_code.txt` in the simulation working directory.

## ISA Encoding (9-bit instructions, 8-bit data path)

| Format | Bit layout | Instructions |
|--------|-----------|--------------|
| R/I-type | `[0 \| opc(4) \| reg/imm(4)]` | all non-branch instructions |
| B-type | `[1 \| cond(2) \| offset(6)]` | `beq`, `bne`, `blt`, `bltu` |

**R/I opcodes** (bits [7:4]): `AND=0x0 XOR=0x1 INV=0x2 ADD=0x3 SUB=0x4 MOV=0x5 STO=0x6 LD=0x7 ST=0x8 CMP=0x9 JMP=0xA SHF=0xB LDI=0xC ADDI=0xD`

- Opcodes 0x0–0xA use bits[3:0] as a register index (r0–r15)
- Opcodes 0xB–0xD use bits[3:0] as a 4-bit immediate (`shf`/`addi`: signed −8..+7; `ldi`: unsigned 0..15)

**Branch offsets**: signed 6-bit PC-relative (−32..+31). Use `jmpl` for longer jumps.

**Special encodings**:
- `done` = `beq 0` = `9'b100000000` — asserts the testbench done flag
- `nop` = `cmp r0` — safe no-op
- `jmpl LABEL rN` — 5-instruction pseudo-op: loads absolute address into rN, then `jmp rN`

## Registers

16 registers (r0–r15), all 8-bit. **r0 is hardwired to 0**. The accumulator (ACC) is a separate implicit destination — `RegFile.sv` maps it to index 15 (`\`define ACC 15`). Most arithmetic instructions write to ACC, while `sto rN` writes ACC into register rN.

**Flags**: `zero_flag`, `sign_flag`, `carry_flag`, `overflow_flag`. Branch conditions: `beq`=Z, `bne`=~Z, `blt`=(S≠V), `bltu`=C.

## Architecture

```
Top.sv
 ├── ProgCtr.sv    — 10-bit PC; resets to 0; Jen asserts absolute jump
 ├── InstROM.sv    — 1024×9-bit ROM; loaded from mach_code.txt via $readmemb
 ├── Ctrl.sv       — decodes mach_code → control signals (WIP / stub)
 ├── RegFile.sv    — 16×8 array; always writes to ACC (index 15) when Wen
 ├── ALU.sv        — 2-bit Aluop: add, left-shift, AND, XOR (partial — not all ISA ops)
 └── DMem.sv       — 256×8-bit data memory; single-ported (one addr for R/W)
```

**Known gaps** (Milestones 2–3 in progress):
- `ALU.sv` only implements 4 operations (Aluop is 2-bit); the full ISA has 14.
- `Ctrl.sv` is a placeholder; control signals are not correctly decoded yet.
- `RegFile.sv` only writes ACC — general register writes (`sto rN`) not yet wired.
- `Top.sv` wiring is incomplete (e.g., `WdatD`, `Addr`, `Jen`, `Rb`, `Wd` connections).

## Python Simulator

`python_implementations/util.py` defines the `Machine` class — a faithful Python model of the ISA. All programs in `python_implementations/` use it to prototype and verify logic before writing assembly or Verilog.

Requires the `bitstring` package (`.venv/bin/activate` to activate virtual evironment).

## Memory Map (all programs start at address 0)

| Program | Input | Output |
|---------|-------|--------|
| 1 (Hamming) | mem[0..63] — 32 signed 16-bit half-words (MSB at even, LSB at odd) | mem[64]=min dist, mem[65]=max dist |
| 2 (Arith diff) | mem[0..63] | mem[66–67]=min abs diff (MSB first), mem[68–69]=max abs diff |
| 3 (Multiply) | mem[0..63] — 16 pairs (A\_N at 4N+0,1; B\_N at 4N+2,3) | mem[64..127] — 16 32-bit products (4 bytes each) |
