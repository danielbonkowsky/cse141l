#!/usr/bin/env python3
"""
DelicateArch Assembler
Converts .asm → 9-bit binary machine code (.mem)

Usage:
    python assembler.py input.asm              # writes input.mem
    python assembler.py input.asm output.mem

============================================================
ISA ENCODING  (matches Milestone 2/3 document)
============================================================
R/I-type: [ 0 | opc(4) | reg/imm(4) ]   (type bit = 0)
B-type:   [ 1 | cond(2)| addr(6)    ]   (type bit = 1)

R/I opcodes (instr[7:4]):
  0000=AND 0001=XOR 0010=INV 0011=ADD 0100=SUB
  0101=MOV 0110=STO 0111=LD  1000=ST  1001=CMP
  1010=JMP 1011=SHF 1100=LDI 1101=ADDI
    • 0x0-0xA → instr[3:0] = register (r0-r15)
    • 0xB-0xD → instr[3:0] = 4-bit immediate

Branch cond (instr[7:6]):
  00=BEQ(Z) 01=BNE(~Z) 10=BLT(S≠V) 11=BLTU(C)
  DONE = beq 0 = 9'b100000000

Registers: r0-r15. r0 hardwired to 0.

shf: positive imm = LEFT shift, negative = RIGHT shift.

============================================================
JMP = ABSOLUTE  (PC = reg), per the texts with Daniel.
  Programs are loaded individually starting at address 0, so every
  loop target fits in an 8-bit register (address ≤ ~200).
  'jmpl LABEL rN' = 5-instruction pseudo-op: loads LABEL's address
  into rN, then jmp rN (PC = rN).

  NOTE: the doc's Section-3 jmp row still says 'PC += R' (relative).
  Update it to 'PC = R' (absolute) to match this assembler + the PC module.
============================================================
"""

import re
import sys
from pathlib import Path

REGS = {f"r{i}": i for i in range(16)}

ALL_OPS = {
    "and": 0x0,
    "xor": 0x1,
    "inv": 0x2,
    "add": 0x3,
    "sub": 0x4,
    "mov": 0x5,
    "sto": 0x6,
    "ld": 0x7,
    "st": 0x8,
    "cmp": 0x9,
    "jmp": 0xA,
    "shf": 0xB,
    "ldi": 0xC,
    "addi": 0xD,
}
IMM_OPS = {"shf", "ldi", "addi"}
B_CONDS = {"beq": 0b00, "bne": 0b01, "blt": 0b10, "bltu": 0b11}
DONE_ENCODING = 0b100000000


def parse_int(s: str) -> int:
    s = s.strip().lstrip("+")
    if s.startswith(("0x", "0X")):
        return int(s, 16)
    if s.startswith(("0b", "0B")):
        return int(s, 2)
    return int(s)


def encode_ri(op: str, field: int) -> int:
    """R/I-type: [ 0 | opc(4) | field(4) ]  field = reg# or 4-bit immediate"""
    return (ALL_OPS[op] << 4) | (field & 0xF)


def encode_b(cond: str, offset: int) -> int:
    """B-type: [ 1 | cond(2) | addr(6) ]"""
    if cond == "beq" and offset == 0:
        return DONE_ENCODING
    if not (-32 <= offset <= 31):
        raise ValueError(
            f"'{cond}' offset {offset} out of range [-32, +31]. Use 'jmpl' for long jumps."
        )
    return (1 << 8) | (B_CONDS[cond] << 6) | (offset & 0x3F)


def build_jmpl(target: int, reg: str) -> list[int]:
    """
    Absolute JMP pseudo-op: load target address into reg, then jmp reg.
    Expands to exactly 5 instructions: ldi hi; shf 4; addi lo; sto rN; jmp rN
    Supports target addresses 0..247 (covers any single program at addr 0).
    """
    if reg not in REGS:
        raise ValueError(f"Unknown register '{reg}'")
    if not (0 <= target <= 247):
        raise ValueError(
            f"jmpl target {target} out of supported range [0, 247]. "
            "Programs should start at address 0 and stay under 248 instructions."
        )
    rn = REGS[reg]
    hi = (target + 8) >> 4  # 0..15 so that lo ∈ [-8, +7]
    lo = target - hi * 16
    return [
        encode_ri("ldi", hi),
        encode_ri("shf", 4),
        encode_ri("addi", lo),
        encode_ri("sto", rn),
        encode_ri("jmp", rn),
    ]


def assemble(source: str):
    lines = source.splitlines()

    def instr_size(line: str) -> int:
        tok = line.split()
        return 5 if tok and tok[0].lower() == "jmpl" else 1

    # ── Pass 1: labels ────────────────────────────────────────────────────────
    labels: dict[str, int] = {}
    clean: list[tuple[int, int, str]] = []
    addr = 0
    for lnum, raw in enumerate(lines, 1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if re.fullmatch(r"[A-Za-z_]\w*:", line):
            labels[line[:-1]] = addr
            continue
        m = re.match(r"^([A-Za-z_]\w*):\s+(.+)$", line)
        if m:
            labels[m.group(1)] = addr
            line = m.group(2).strip()
        # allow several instructions on one line separated by ';'
        for piece in line.split(";"):
            piece = piece.strip()
            if not piece:
                continue
            clean.append((lnum, addr, piece))
            addr += instr_size(piece)

    # ── Pass 2: encode ────────────────────────────────────────────────────────
    output: list[tuple[int, str, str]] = []
    for lnum, addr, line in clean:
        tokens = line.split()
        op = tokens[0].lower()
        try:
            if op == "nop":
                output.append(
                    (addr, format(encode_ri("cmp", 0), "09b"), line)
                )  # cmp r0
            elif op == "done":
                output.append((addr, format(DONE_ENCODING, "09b"), line))
            elif op == "jmpl":
                if len(tokens) < 3:
                    raise SyntaxError("jmpl requires: jmpl LABEL rN")
                lbl, reg = tokens[1], tokens[2].lower().rstrip(",")
                T = labels[lbl] if lbl in labels else parse_int(lbl)
                for i, bits in enumerate(build_jmpl(T, reg)):
                    src = line if i == 0 else f"  [{line}] +{i}"
                    output.append((addr + i, format(bits, "09b"), src))
            elif op in ALL_OPS:
                if op in IMM_OPS:
                    imm = parse_int(tokens[1])
                    if op == "ldi" and not (0 <= imm <= 15):
                        raise ValueError(f"ldi immediate {imm} out of range [0, 15]")
                    if op in ("shf", "addi") and not (-8 <= imm <= 7):
                        raise ValueError(
                            f"'{op}' immediate {imm} out of range [-8, +7]"
                        )
                    bits = encode_ri(op, imm)
                else:
                    if op == "inv":
                        reg_num = 0
                    else:
                        reg = tokens[1].lower().rstrip(",")
                        if reg not in REGS:
                            raise ValueError(f"Unknown register '{reg}'")
                        reg_num = REGS[reg]
                    bits = encode_ri(op, reg_num)
                output.append((addr, format(bits, "09b"), line))
            elif op in B_CONDS:
                target = tokens[1]
                offset = (
                    (labels[target] - addr - 1)
                    if target in labels
                    else parse_int(target)
                )
                output.append((addr, format(encode_b(op, offset), "09b"), line))
            elif op == ".word":
                output.append((addr, format(parse_int(tokens[1]) & 0x1FF, "09b"), line))
            else:
                raise SyntaxError(f"Unknown instruction '{op}'")
        except (KeyError, SyntaxError, ValueError) as e:
            print(f"Error line {lnum}: {e}\n  > {line}", file=sys.stderr)
            sys.exit(1)

    return output, labels


def main():
    if len(sys.argv) < 2:
        print("Usage: python assembler.py <input.asm> [output.mem]")
        sys.exit(1)
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else in_path.with_suffix(".mem")
    if not in_path.exists():
        print(f"Error: {in_path} not found", file=sys.stderr)
        sys.exit(1)

    encoded, labels = assemble(in_path.read_text())
    with open(out_path, "w") as f:
        for _, b, _ in encoded:
            f.write(b + "\n")

    print(f"{'Addr':>4}  {'Binary':>9}  {'Hex':>5}  Source")
    print("─" * 65)
    for a, b, src in encoded:
        print(f"{a:>4}  {b}  0x{int(b, 2):03X}  {src}")
    print(f"\n{len(encoded)} instructions  →  {out_path}")
    if labels:
        print("\nLabels:")
        for name, a in sorted(labels.items(), key=lambda x: x[1]):
            print(f"  {a:>4}  {name}")


if __name__ == "__main__":
    main()
