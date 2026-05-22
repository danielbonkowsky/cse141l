#!/usr/bin/env python3
"""
DelicateArch Assembler
Converts DelicateArch assembly (.asm) to 9-bit binary machine code (.mem).

Usage:
    python assembler.py input.asm              # outputs input.mem
    python assembler.py input.asm output.mem   # outputs output.mem

ISA Encoding:
    R-type: [ 00 | opc(4) | reg(3) ]   bits[8:7]=00, bits[6:3]=opcode, bits[2:0]=reg
    I-type: [ 01 | opc(3) | imm(4) ]   bits[8:7]=01, bits[6:4]=opcode, bits[3:0]=imm
    B-type: [ 1  | cond(2)| addr(6)]   bit[8]=1,     bits[7:6]=cond,   bits[5:0]=offset

Instructions:
    R-type (reg argument):   and, xor, add, sub, mov, sto, ld, st, cmp, jmp
    R-type (no argument):    inv
    I-type (imm argument):   shf (-8 to +7), ldi (0 to 15), addi (-8 to +7)
    B-type (label/offset):   beq, blt, bcs
    Pseudo-instructions:     nop (= cmp r0), done (= beq 0, signals testbench)

Assembly Syntax:
    - Comments start with #
    - Labels end with : and can be on their own line or same line as instruction
    - Registers: r0, r1, r2, r3, r4, r5, r6, r7  (r0 hardwired to 0)
    - Immediates: decimal (5, -3), hex (0xFF), binary (0b1010)
    - Branch targets: label name or signed integer offset

Example:
    # initialize
    ldi 0
    sto r1          # r1 = 0

    LOOP:
      mov r1
      addi 1        # acc = r1 + 1
      sto r1
      cmp r2        # acc - r2
      blt LOOP      # if acc < r2, loop back

    done            # signal completion
"""

import sys
import re
from pathlib import Path


# ─── Register table ──────────────────────────────────────────────────────────

REGS = {f'r{i}': i for i in range(8)}

# ─── Opcode tables ───────────────────────────────────────────────────────────

R_OPS = {
    'and': 0b0000,  # ACC &= reg
    'xor': 0b0001,  # ACC ^= reg
    'inv': 0b0010,  # ACC = ~ACC     (reg field unused, set to 000)
    'add': 0b0011,  # ACC += reg     sets C, Z, S, OV
    'sub': 0b0100,  # ACC -= reg     sets C, Z, S, OV
    'mov': 0b0101,  # ACC  = reg
    'sto': 0b0110,  # reg  = ACC
    'ld':  0b0111,  # ACC  = mem[reg]
    'st':  0b1000,  # mem[reg] = ACC
    'cmp': 0b1001,  # ACC - reg, sets flags only (no writeback)
    'jmp': 0b1010,  # PC += reg      (signed 8-bit relative jump)
}

I_OPS = {
    'shf':  0b000,  # ACC <<= imm (positive) or >>= |imm| (negative), 4-bit signed
    'ldi':  0b001,  # ACC  = imm    (4-bit unsigned, 0-15)
    'addi': 0b010,  # ACC += imm    (4-bit signed, -8 to +7)
}

B_CONDS = {
    'beq': 0b00,    # branch if Zero flag set    (after cmp: ACC == reg)
    'blt': 0b01,    # branch if Sign flag set    (after cmp: ACC < reg, signed)
    'bcs': 0b10,    # branch if Carry flag set   (after cmp: ACC < reg, unsigned)
}

# Encoding for beq 0 = done signal to testbench
DONE_ENCODING = 0b100000000  # 1_00_000000


# ─── Encoding helpers ─────────────────────────────────────────────────────────

def parse_int(s: str) -> int:
    """Parse integer literal: decimal, 0x hex, or 0b binary."""
    s = s.strip().lstrip('+')  # strip leading +
    if s.startswith(('0x', '0X')):
        return int(s, 16)
    elif s.startswith(('0b', '0B')):
        return int(s, 2)
    else:
        return int(s)


def encode_r(op: str, reg: str = 'r0') -> int:
    """
    R-type: [ 00 | opc(4) | reg(3) ]
    Bits: [8:7]=00, [6:3]=opcode, [2:0]=register
    """
    if reg not in REGS:
        raise ValueError(f"Unknown register '{reg}'. Valid: r0-r7")
    return (0b00 << 7) | (R_OPS[op] << 3) | REGS[reg]


def encode_i(op: str, imm_int: int) -> int:
    """
    I-type: [ 01 | opc(3) | imm(4) ]
    Bits: [8:7]=01, [6:4]=opcode, [3:0]=immediate
    shf/addi: signed 4-bit (-8 to +7)
    ldi:      unsigned 4-bit (0 to 15)
    """
    if op in ('shf', 'addi'):
        if not (-8 <= imm_int <= 7):
            raise ValueError(
                f"'{op}' immediate {imm_int} out of signed range [-8, 7]"
            )
        imm_4 = imm_int & 0xF  # two's complement 4-bit
    else:  # ldi
        if not (0 <= imm_int <= 15):
            raise ValueError(
                f"'ldi' immediate {imm_int} out of unsigned range [0, 15]"
            )
        imm_4 = imm_int
    return (0b01 << 7) | (I_OPS[op] << 4) | imm_4


def encode_b(op: str, offset: int) -> int:
    """
    B-type: [ 1 | cond(2) | addr(6) ]
    Bits: [8]=1, [7:6]=condition, [5:0]=signed PC-relative offset
    Range: -32 to +31 instructions
    Special: beq with offset=0 → done signal
    """
    if op == 'beq' and offset == 0:
        return DONE_ENCODING
    if not (-32 <= offset <= 31):
        raise ValueError(
            f"'{op}' offset {offset} out of range [-32, 31]. "
            f"Use 'jmp rN' for larger jumps."
        )
    offset_6 = offset & 0x3F  # 6-bit two's complement
    return (0b1 << 8) | (B_CONDS[op] << 6) | offset_6


# ─── Assembler ────────────────────────────────────────────────────────────────

def assemble(source: str):
    """
    Two-pass assembler.

    Pass 1: strip comments, collect labels, compute instruction addresses.
    Pass 2: encode each instruction using resolved label addresses.

    Returns:
        instructions: list of (addr, binary_str, original_line)
        labels: dict of label -> address
    """
    lines = source.splitlines()

    # ── Pass 1: collect labels ────────────────────────────────────────────────
    labels: dict[str, int] = {}
    clean_lines: list[tuple[int, int, str]] = []  # (line_num, addr, text)
    addr = 0

    for line_num, raw_line in enumerate(lines, start=1):
        # strip inline comments
        line = raw_line.split('#')[0].strip()
        if not line:
            continue

        # handle label on its own line:  LABEL:
        if re.fullmatch(r'[A-Za-z_]\w*:', line):
            label = line[:-1]
            if label in labels:
                raise SyntaxError(
                    f"Line {line_num}: duplicate label '{label}'"
                )
            labels[label] = addr
            continue

        # handle label + instruction on same line:  LABEL: instruction ...
        label_match = re.match(r'^([A-Za-z_]\w*):\s+(.+)$', line)
        if label_match:
            label, rest = label_match.group(1), label_match.group(2).strip()
            if label in labels:
                raise SyntaxError(
                    f"Line {line_num}: duplicate label '{label}'"
                )
            labels[label] = addr
            line = rest

        clean_lines.append((line_num, addr, line))
        addr += 1

    # ── Pass 2: encode instructions ───────────────────────────────────────────
    output: list[tuple[int, str, str]] = []

    for line_num, addr, line in clean_lines:
        tokens = line.split()
        op = tokens[0].lower()

        try:
            # ── Pseudo-instructions ──────────────────────────────────────────
            if op == 'nop':
                # nop = cmp r0 (sets flags but doesn't write, safe as padding)
                bits = encode_r('cmp', 'r0')

            elif op == 'done':
                # done = beq 0 = special encoding that asserts done flag
                bits = DONE_ENCODING

            # ── R-type instructions ──────────────────────────────────────────
            elif op in R_OPS:
                if op == 'inv':
                    # inv has no register argument
                    bits = encode_r('inv', 'r0')
                else:
                    if len(tokens) < 2:
                        raise SyntaxError(f"'{op}' requires a register argument")
                    reg = tokens[1].lower().rstrip(',')
                    bits = encode_r(op, reg)

            # ── I-type instructions ──────────────────────────────────────────
            elif op in I_OPS:
                if len(tokens) < 2:
                    raise SyntaxError(f"'{op}' requires an immediate argument")
                imm_int = parse_int(tokens[1])
                bits = encode_i(op, imm_int)

            # ── B-type instructions ──────────────────────────────────────────
            elif op in B_CONDS:
                if len(tokens) < 2:
                    raise SyntaxError(f"'{op}' requires a label or offset")
                target = tokens[1]
                if target in labels:
                    # PC-relative: target_addr - current_addr
                    offset = labels[target] - addr
                else:
                    offset = parse_int(target)
                bits = encode_b(op, offset)

            # ── Raw binary literal (for debugging/NOPs) ──────────────────────
            elif op == '.word':
                if len(tokens) < 2:
                    raise SyntaxError("'.word' requires a value")
                bits = parse_int(tokens[1]) & 0x1FF  # mask to 9 bits

            else:
                raise SyntaxError(f"Unknown instruction '{op}'")

            binary_str = format(bits, '09b')
            output.append((addr, binary_str, line))

        except SyntaxError:
            raise
        except ValueError as e:
            raise ValueError(f"Line {line_num}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Line {line_num}: unexpected error: {e}") from e

    return output, labels


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Usage: python assembler.py <input.asm> [output.mem]")
        sys.exit(1)

    input_path  = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 \
                  else input_path.with_suffix('.mem')

    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    source = input_path.read_text()

    try:
        encoded, labels = assemble(source)
    except (SyntaxError, ValueError, RuntimeError) as e:
        print(f"Assembly failed: {e}", file=sys.stderr)
        sys.exit(1)

    # write .mem file: one 9-bit binary string per line
    # compatible with SystemVerilog $readmemb()
    with open(output_path, 'w') as f:
        for _, binary_str, _ in encoded:
            f.write(binary_str + '\n')

    # print annotated listing to stdout
    col = 55
    print(f"{'Addr':>4}  {'[8:0] Binary':>9}  {'Hex':>3}  {'Instruction'}")
    print('─' * 60)
    for addr, binary_str, src in encoded:
        hex_val = int(binary_str, 2)
        print(f"{addr:>4}  {binary_str}  0x{hex_val:03X}  {src}")

    print()
    print(f"Assembled {len(encoded)} instruction(s)  →  {output_path}")

    if labels:
        print()
        print("Labels:")
        for name, laddr in sorted(labels.items(), key=lambda x: x[1]):
            print(f"  {laddr:>4}  {name}")


if __name__ == '__main__':
    main()
