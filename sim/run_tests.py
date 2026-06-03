#!/usr/bin/env python3
"""
DelicateArch ISA simulator testbench — Programs 1 & 2
Replicates the logic of test_bench_new.sv and test_bench2_new.sv.
Runs the assembled .mem programs against the 10 test files and reports pass/fail.
"""
import sys, os

TESTBENCH_DIR = os.path.join(os.path.dirname(__file__), '..', 'testbenches', 'test_files')
PROG1_MEM = os.path.join(os.path.dirname(__file__), '..', 'program1', 'program1.mem')
PROG2_MEM = os.path.join(os.path.dirname(__file__), '..', 'program2', 'program2.mem')
NUM_TESTS = 10

# ── ISA Simulator ────────────────────────────────────────────────────────────

def load_program(path):
    with open(path) as f:
        return [int(l.strip(), 2) for l in f if l.strip()]

def load_test(path):
    mem = [0] * 256
    with open(path) as f:
        for i, line in enumerate(f):
            s = line.strip()
            if s:
                mem[i] = int(s, 2)
    return mem

def run(inst_mem, data_mem, max_cycles=2_000_000):
    """Simulate one run of inst_mem on data_mem; returns (data_mem, cycles) or raises."""
    reg = [0] * 16   # r0 hardwired to 0
    acc = 0
    pc = 0
    zero_f = carry_f = sign_f = ovfl_f = 0

    for cycle in range(max_cycles):
        if pc >= len(inst_mem):
            raise RuntimeError(f"PC {pc} out of range after {cycle} cycles")
        ir = inst_mem[pc]

        # done = beq offset=0
        if ir == 0b100000000:
            return data_mem, cycle

        is_branch = (ir >> 8) & 1
        opc       = (ir >> 4) & 0xF
        reg_imm   = ir & 0xF
        cond      = (ir >> 6) & 0x3
        boffset   = ir & 0x3F

        rn = 0 if reg_imm == 0 else reg[reg_imm]

        if is_branch:
            # sign-extend 6-bit offset
            off = boffset if boffset < 32 else boffset - 64
            taken = False
            if   cond == 0b00: taken = bool(zero_f)
            elif cond == 0b01: taken = not bool(zero_f)
            elif cond == 0b10: taken = (sign_f != ovfl_f)
            elif cond == 0b11: taken = bool(carry_f)
            pc = (pc + off) if taken else (pc + 1)
        else:
            # R/I type — compute result and update state
            write_acc  = True
            write_zs   = False  # update zero / sign flags
            write_co   = False  # update carry / overflow flags
            clear_co   = False  # clear carry / overflow (AND, XOR)
            skip_acc   = False  # STO, ST, JMP, CMP

            if opc == 0x0:   # AND
                result = acc & rn; write_zs = True; clear_co = True
            elif opc == 0x1: # XOR
                result = acc ^ rn; write_zs = True; clear_co = True
            elif opc == 0x2: # INV  (preserves flags)
                result = (~acc) & 0xFF
            elif opc == 0x3: # ADD
                r16 = acc + rn
                new_c = 1 if r16 > 255 else 0
                result = r16 & 0xFF
                new_v = 1 if (acc >> 7 == rn >> 7) and ((result >> 7) != (acc >> 7)) else 0
                carry_f, ovfl_f = new_c, new_v; write_zs = True; write_co = True
            elif opc == 0x4: # SUB
                r16 = acc - rn
                new_c = 1 if acc < rn else 0   # borrow = unsigned less
                result = r16 & 0xFF
                new_v = 1 if ((acc >> 7) != (rn >> 7)) and ((result >> 7) != (acc >> 7)) else 0
                carry_f, ovfl_f = new_c, new_v; write_zs = True; write_co = True
            elif opc == 0x5: # MOV  (preserves flags)
                result = rn
            elif opc == 0x6: # STO  (preserves flags)
                if reg_imm != 0:
                    reg[reg_imm] = acc
                skip_acc = True
            elif opc == 0x7: # LD   (preserves flags)
                result = data_mem[rn]
            elif opc == 0x8: # ST   (preserves flags)
                data_mem[rn] = acc; skip_acc = True
            elif opc == 0x9: # CMP
                r16 = acc - rn
                new_c = 1 if acc < rn else 0
                result = r16 & 0xFF
                new_v = 1 if ((acc >> 7) != (rn >> 7)) and ((result >> 7) != (acc >> 7)) else 0
                carry_f, ovfl_f = new_c, new_v; write_zs = True; write_co = True
                skip_acc = True
            elif opc == 0xA: # JMP  (absolute, preserves flags)
                pc = rn; continue
            elif opc == 0xB: # SHF  (updates Z,S; preserves C,V)
                simm4 = reg_imm if reg_imm < 8 else reg_imm - 16
                if simm4 >= 0:
                    result = (acc << simm4) & 0xFF
                else:
                    result = acc >> (-simm4)
                write_zs = True
            elif opc == 0xC: # LDI  (preserves flags)
                result = reg_imm  # unsigned 0..15
            elif opc == 0xD: # ADDI
                simm4 = reg_imm if reg_imm < 8 else reg_imm - 16
                r16 = acc + simm4
                new_c = 1 if r16 > 255 or r16 < 0 else 0
                result = r16 & 0xFF
                new_v = 1 if ((acc >> 7) == (simm4 >> 7 & 1)) and ((result >> 7) != (acc >> 7)) else 0
                carry_f, ovfl_f = new_c, new_v; write_zs = True; write_co = True
            else:
                result = 0

            if not skip_acc:
                acc = result
            if write_zs:
                zero_f = 1 if result == 0 else 0
                sign_f = (result >> 7) & 1
            if write_co:
                pass  # already updated above in the specific cases
            if clear_co:
                carry_f = 0; ovfl_f = 0

            pc += 1

    raise RuntimeError(f"Exceeded {max_cycles} cycles (infinite loop?)")


# ── Testbench helpers ────────────────────────────────────────────────────────

def ham(a: int, b: int) -> int:
    """Hamming distance between two 16-bit values."""
    x = a ^ b
    count = 0
    while x:
        count += x & 1
        x >>= 1
    return count

def abs_dist(a: int, b: int) -> int:
    """Unsigned magnitude of difference between two signed 16-bit values."""
    sa = a if a < 0x8000 else a - 0x10000
    sb = b if b < 0x8000 else b - 0x10000
    return abs(sa - sb)

def read_pairs(mem):
    """Extract 32 16-bit values from mem[0..63]."""
    return [(mem[2*i] << 8) | mem[2*i+1] for i in range(32)]


# ── Program 1 testbench (matches test_bench_new.sv) ─────────────────────────

def run_prog1(inst_mem):
    print("=" * 60)
    print("PROGRAM 1 — min/max Hamming distance")
    print("=" * 60)
    min_pass = max_pass = 0

    for t in range(NUM_TESTS):
        test_file = os.path.join(TESTBENCH_DIR, f'test{t}.txt')
        mem = load_test(test_file)

        # Testbench preloads
        mem[64] = 16    # preset min to max possible
        for r in range(65, 256):
            mem[r] = 0  # preset max to min possible

        # Compute correct answers (testbench reference)
        vals = read_pairs(mem)
        ref_min = 16; ref_max = 0
        min1 = min2 = max1 = max2 = 0
        for j in range(32):
            for k in range(j+1, 32):
                d = ham(vals[j], vals[k])
                if d < ref_min: ref_min = d; min2 = j; min1 = k
                if d > ref_max: ref_max = d; max2 = j; max1 = k

        # Run the assembled program
        try:
            result_mem, cycles = run(inst_mem, mem[:])  # copy so preloads persist
            dut_min = result_mem[64]
            dut_max = result_mem[65]
        except RuntimeError as e:
            print(f"  test{t}: ERROR — {e}")
            continue

        # Check
        ok_min = (ref_min == dut_min)
        ok_max = (ref_max == dut_max)
        if ok_min: min_pass += 1
        if ok_max: max_pass += 1

        status_min = "good" if ok_min else f"FAIL (expected {ref_min}, got {dut_min})"
        status_max = "good" if ok_max else f"FAIL (expected {ref_max}, got {dut_max})"
        print(f"  test{t}: Min={status_min}  Max={status_max}  ({cycles} cycles)")

    print(f"\nMinimum correct {min_pass}/{NUM_TESTS}")
    print(f"Maximum correct {max_pass}/{NUM_TESTS}")
    return min_pass, max_pass


# ── Program 2 testbench (matches test_bench2_new.sv) ────────────────────────

def run_prog2(inst_mem):
    print()
    print("=" * 60)
    print("PROGRAM 2 — min/max arithmetic distance")
    print("=" * 60)
    min_pass = max_pass = 0

    for t in range(NUM_TESTS):
        test_file = os.path.join(TESTBENCH_DIR, f'test{t}.txt')
        mem = load_test(test_file)

        # Testbench preloads (note: [64:65] intentionally not touched here)
        mem[66] = 0xFF; mem[67] = 0xFF   # preset min to 0xFFFF
        for r in range(68, 256):
            mem[r] = 0                    # preset max to 0

        # Correct answers
        vals = read_pairs(mem)
        ref_min = 0xFFFF; ref_max = 0x0000
        min1 = min2 = max1 = max2 = 0
        for j in range(32):
            for k in range(j+1, 32):
                d = abs_dist(vals[j], vals[k])
                if d < ref_min: ref_min = d; min2 = j; min1 = k
                if d > ref_max: ref_max = d; max2 = j; max1 = k

        # Run the assembled program
        try:
            result_mem, cycles = run(inst_mem, mem[:])
            dut_min = (result_mem[66] << 8) | result_mem[67]
            dut_max = (result_mem[68] << 8) | result_mem[69]
        except RuntimeError as e:
            print(f"  test{t}: ERROR — {e}")
            continue

        ok_min = (ref_min == dut_min)
        ok_max = (ref_max == dut_max)
        if ok_min: min_pass += 1
        if ok_max: max_pass += 1

        status_min = "good" if ok_min else f"FAIL (expected {ref_min}, got {dut_min})"
        status_max = "good" if ok_max else f"FAIL (expected {ref_max}, got {dut_max})"
        print(f"  test{t}: Min={status_min}  Max={status_max}  ({cycles} cycles)")

    print(f"\nMinimum correct {min_pass}/{NUM_TESTS}")
    print(f"Maximum correct {max_pass}/{NUM_TESTS}")
    return min_pass, max_pass


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    prog1 = load_program(PROG1_MEM)
    prog2 = load_program(PROG2_MEM)

    p1_min, p1_max = run_prog1(prog1)
    p2_min, p2_max = run_prog2(prog2)

    print()
    print("=" * 60)
    print("SUMMARY")
    print(f"  Program 1  Min: {p1_min}/10   Max: {p1_max}/10")
    print(f"  Program 2  Min: {p2_min}/10   Max: {p2_max}/10")
    print("=" * 60)
