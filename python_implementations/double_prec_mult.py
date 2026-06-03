"""
Double-precision (16x16 bits = 32-bit product) two's complement
multiplication using shift-and-add (a direct c=a*b - multiplication operation
is not allowed, although this can be a programming macro that breaks down
into a subroutine).
Operands are stored in memory locations 0-3, 4-7, ..., 60-63, where the
format is:
mem[4N+0]: most significant (signed) byte of operand A_N
mem[4N+1]: least significant (unsigned) byte of operand A_N
mem[4N+2]: most significant (signed) byte of operand B_N
mem[4N+3]: least significant (unsigned) byte of operand B_N

All of these independent variable values will be injected directly into your
data memory to start the program. You will then return your results to
data_mem 64-127, where the format is:
mem[64+4N+0]: most significant (signed) byte of product of A_N * B_N
mem[64+4N+1]: second (unsigned) byte of same product
mem[64+4N+2]: third (unsigned) byte
mem[64+4N+3]: least significant byte (unsigned)

Register allocation:
    r0  = hardwired 0
    r1  = outer loop index N (0..15)
    r2  = A_hi (signed MSB of A); scratch after multiply setup
    r3  = shifted_A byte 0 / LSB (initialized to A_lo magnitude)
    r4  = B_hi (right-shifted during inner loop)
    r5  = B_lo (right-shifted first, then done)
    r6  = address scratch
    r7  = result_sign (0 = positive, 1 = negative)
    r8  = product byte 3 (MSB, signed)
    r9  = product byte 2
    r10 = product byte 1
    r11 = product byte 0 (LSB)
    r12 = shifted_A byte 3 (MSB, starts 0)
    r13 = shifted_A byte 2 (starts 0)
    r14 = shifted_A byte 1 (initialized to A_hi magnitude)

Algorithm: sign-magnitude shift-and-add.
  1. Detect signs of A and B from their MSBs (left-shift, check carry).
  2. Negate each to get unsigned magnitude if negative.
  3. Multiply magnitudes: for each of 16 bits of B (LSB first), if the bit is
     set add the current shifted_A value to the product, then left-shift
     shifted_A by 1.
  4. If result should be negative, two's-complement negate the 32-bit product.
"""

import sys

from bitstring import BitArray
from util import Machine


# ── Helpers ──────────────────────────────────────────────────────────────────

def negate_16(vm: Machine, reg_hi: str, reg_lo: str) -> None:
    """Two's complement negate of a 16-bit value in [reg_hi, reg_lo]."""
    vm.mov_R(reg_lo)
    vm.inv_R()
    vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R(reg_lo)
    carry = vm.carry_flag[0]

    vm.mov_R(reg_hi)
    vm.inv_R()
    if carry:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R(reg_hi)


def add_shifted_a_to_product(vm: Machine) -> None:
    """Add shifted_A [r12, r13, r14, r3] to product [r8, r9, r10, r11].

    Carries are captured immediately after each add, before the conditional
    addi, so a second carry from addi cannot corrupt the chain. This is safe
    because addi 1 on a value whose LSB is 0 (after left-shift) cannot itself
    overflow — but here we're adding to an accumulated byte, so we must still
    propagate with Python booleans.
    """
    # byte 0 (LSB): r11 += r3
    vm.mov_R("r11")
    vm.add_R("r3")
    vm.sto_R("r11")
    c0 = vm.carry_flag[0]

    # byte 1: r10 += r14, then propagate c0
    vm.mov_R("r10")
    vm.add_R("r14")
    c1 = vm.carry_flag[0]
    if c0:
        vm.addi_I(BitArray(uint=1, length=8))
        c1 = c1 or vm.carry_flag[0]
    vm.sto_R("r10")

    # byte 2: r9 += r13, then propagate c1
    vm.mov_R("r9")
    vm.add_R("r13")
    c2 = vm.carry_flag[0]
    if c1:
        vm.addi_I(BitArray(uint=1, length=8))
        c2 = c2 or vm.carry_flag[0]
    vm.sto_R("r9")

    # byte 3 (MSB): r8 += r12, then propagate c2
    vm.mov_R("r8")
    vm.add_R("r12")
    if c2:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r8")


def left_shift_a_by_1(vm: Machine) -> None:
    """Left-shift shifted_A [r12, r13, r14, r3] by 1 bit as a 32-bit value.

    After each left-shift by 1, the LSB of the result is 0, so addi 1 (to
    inject an incoming carry) cannot itself overflow — the carry chain is safe.
    """
    # r3 (LSB): carry = MSB of r3 (bit that shifts into r14)
    vm.mov_R("r3")
    vm.shf_I(BitArray(int=1, length=8))
    vm.sto_R("r3")
    c0 = vm.carry_flag[0]

    # r14: carry = MSB of r14; inject c0 into LSB
    vm.mov_R("r14")
    vm.shf_I(BitArray(int=1, length=8))
    c1 = vm.carry_flag[0]
    if c0:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r14")

    # r13: carry = MSB of r13; inject c1
    vm.mov_R("r13")
    vm.shf_I(BitArray(int=1, length=8))
    c2 = vm.carry_flag[0]
    if c1:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r13")

    # r12 (MSB): inject c2 (overflow into a 5th byte is discarded)
    vm.mov_R("r12")
    vm.shf_I(BitArray(int=1, length=8))
    if c2:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r12")


def negate_32(vm: Machine) -> None:
    """Two's complement negate the 32-bit product in [r8, r9, r10, r11]."""
    vm.mov_R("r11")
    vm.inv_R()
    vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r11")
    c = vm.carry_flag[0]

    vm.mov_R("r10")
    vm.inv_R()
    if c:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r10")
    c = vm.carry_flag[0]

    vm.mov_R("r9")
    vm.inv_R()
    if c:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r9")
    c = vm.carry_flag[0]

    vm.mov_R("r8")
    vm.inv_R()
    if c:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r8")


def multiply_16x16(vm: Machine) -> None:
    """Signed 16×16 → 32-bit shift-and-add multiply.

    Inputs:  A in [r2 (hi, signed), r3 (lo, unsigned)]
             B in [r4 (hi, signed), r5 (lo, unsigned)]
    Output:  32-bit product in [r8 (MSB), r9, r10, r11 (LSB)]
    Scratch: r7 (result_sign), r12-r14 (upper shifted_A bytes)
    """
    # ── Determine result sign ────────────────────────────────────────────────
    # Left-shift MSB byte; carry = sign bit (1 = negative)
    vm.mov_R("r2")
    vm.shf_I(BitArray(int=1, length=8))
    a_neg = vm.carry_flag[0]

    vm.mov_R("r4")
    vm.shf_I(BitArray(int=1, length=8))
    b_neg = vm.carry_flag[0]

    result_neg = a_neg ^ b_neg
    if result_neg:
        vm.ldi_I(BitArray(uint=1, length=8))
    else:
        vm.ldi_I(BitArray(uint=0, length=8))
    vm.sto_R("r7")

    # ── Convert operands to unsigned magnitudes ──────────────────────────────
    if a_neg:
        negate_16(vm, "r2", "r3")
    if b_neg:
        negate_16(vm, "r4", "r5")

    # ── Initialize product = 0 ───────────────────────────────────────────────
    vm.ldi_I(BitArray(uint=0, length=8))
    vm.sto_R("r8")
    vm.sto_R("r9")
    vm.sto_R("r10")
    vm.sto_R("r11")

    # ── Initialize shifted_A = [0, 0, |A_hi|, |A_lo|] ───────────────────────
    # r3 already holds |A_lo|; move |A_hi| (r2) into r14, zero r12/r13
    vm.ldi_I(BitArray(uint=0, length=8))
    vm.sto_R("r12")
    vm.sto_R("r13")
    vm.mov_R("r2")
    vm.sto_R("r14")
    # r3 = |A_lo| (unchanged) ✓

    # ── Process B_lo (bits 0-7 of B) ────────────────────────────────────────
    for _ in range(8):
        vm.mov_R("r5")
        vm.shf_I(BitArray(int=-1, length=8))   # right-shift; carry = bit 0 of B
        vm.sto_R("r5")
        if vm.carry_flag[0]:
            add_shifted_a_to_product(vm)
        left_shift_a_by_1(vm)

    # ── Process B_hi (bits 8-15 of B) ───────────────────────────────────────
    for _ in range(8):
        vm.mov_R("r4")
        vm.shf_I(BitArray(int=-1, length=8))   # right-shift; carry = bit 0 of B_hi
        vm.sto_R("r4")
        if vm.carry_flag[0]:
            add_shifted_a_to_product(vm)
        left_shift_a_by_1(vm)

    # ── Apply sign to product ────────────────────────────────────────────────
    # Right-shift r7 by 1: carry = LSB of r7 = result_neg (0 or 1)
    vm.mov_R("r7")
    vm.shf_I(BitArray(int=-1, length=8))
    if vm.carry_flag[0]:
        negate_32(vm)


# ── Main ─────────────────────────────────────────────────────────────────────

def main(vm: Machine | None = None) -> int:
    if vm is None:
        vm = Machine()

    for n in range(16):
        # r1 = n
        vm.ldi_I(BitArray(uint=n, length=8))
        vm.sto_R("r1")

        # base = 4*n: ldi n → ACC, shf +2
        vm.shf_I(BitArray(int=2, length=8))
        vm.sto_R("r6")                          # r6 = 4*n

        # Load A: mem[4n+0] = A_hi, mem[4n+1] = A_lo
        vm.ld_R("r6")
        vm.sto_R("r2")                          # r2 = A_hi
        vm.mov_R("r6")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r6")
        vm.ld_R("r6")
        vm.sto_R("r3")                          # r3 = A_lo

        # Load B: mem[4n+2] = B_hi, mem[4n+3] = B_lo
        vm.mov_R("r6")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r6")
        vm.ld_R("r6")
        vm.sto_R("r4")                          # r4 = B_hi
        vm.mov_R("r6")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r6")
        vm.ld_R("r6")
        vm.sto_R("r5")                          # r5 = B_lo

        multiply_16x16(vm)

        # out_base = 64 + 4*n
        vm.mov_R("r1")
        vm.shf_I(BitArray(int=2, length=8))     # ACC = 4*n
        vm.sto_R("r6")
        vm.ldi_I(BitArray(uint=64, length=8))   # ACC = 64
        vm.add_R("r6")
        vm.sto_R("r6")                          # r6 = 64 + 4*n

        vm.mov_R("r8"); vm.st_R("r6")
        vm.mov_R("r6"); vm.addi_I(BitArray(uint=1, length=8)); vm.sto_R("r6")
        vm.mov_R("r9"); vm.st_R("r6")
        vm.mov_R("r6"); vm.addi_I(BitArray(uint=1, length=8)); vm.sto_R("r6")
        vm.mov_R("r10"); vm.st_R("r6")
        vm.mov_R("r6"); vm.addi_I(BitArray(uint=1, length=8)); vm.sto_R("r6")
        vm.mov_R("r11"); vm.st_R("r6")

    return 0


# ── Tests ─────────────────────────────────────────────────────────────────────

def test() -> None:
    import random as _random

    def _load_pair(vm: Machine, n: int, a: int, b: int) -> None:
        """Load a signed 16-bit pair (a, b) into mem[4n..4n+3]."""
        a_u = a & 0xFFFF
        b_u = b & 0xFFFF
        vm.mem[4 * n + 0] = BitArray(uint=(a_u >> 8) & 0xFF, length=8)
        vm.mem[4 * n + 1] = BitArray(uint=a_u & 0xFF, length=8)
        vm.mem[4 * n + 2] = BitArray(uint=(b_u >> 8) & 0xFF, length=8)
        vm.mem[4 * n + 3] = BitArray(uint=b_u & 0xFF, length=8)

    def _read_product(vm: Machine, n: int) -> int:
        """Read the 32-bit signed product from mem[64+4n..64+4n+3]."""
        base = 64 + 4 * n
        raw = (
            (vm.mem[base + 0].uint << 24)
            | (vm.mem[base + 1].uint << 16)
            | (vm.mem[base + 2].uint << 8)
            | vm.mem[base + 3].uint
        )
        # sign-extend to Python int
        return raw if raw < (1 << 31) else raw - (1 << 32)

    def _run(pairs: list[tuple[int, int]], label: str) -> None:
        vm = Machine()
        for n, (a, b) in enumerate(pairs):
            _load_pair(vm, n, a, b)
        main(vm)
        for n, (a, b) in enumerate(pairs):
            expected = a * b
            got = _read_product(vm, n)
            assert got == expected, (
                f"{label} pair {n}: {a} × {b} = {expected}, got {got}"
            )

    # fixed cases (all 16 slots filled with the same pair to keep it simple)
    _run([(0, 0)] * 16,                                        "all zeros")
    _run([(1, 1)] * 16,                                        "1 × 1")
    _run([(256, 256)] * 16,                                    "256 × 256 = 65536")
    _run([(-1, 1)] * 16,                                       "-1 × 1 = -1")
    _run([(-1, -1)] * 16,                                      "-1 × -1 = 1")
    _run([(0x7FFF, 0x7FFF)] * 16,                              "max_pos × max_pos")
    _run([(-0x8000, -0x8000)] * 16,                            "min × min")
    _run([(-0x8000, 1)] * 16,                                  "min × 1")
    _run([(0x7FFF, -0x8000)] * 16,                             "max_pos × min")
    _run([(100, -200)] * 16,                                   "100 × -200")

    # 16 distinct pairs in one run
    mixed = [
        (0, 0), (1, 1), (-1, 1), (-1, -1),
        (256, 256), (0x7FFF, 1), (-0x8000, 1), (0x7FFF, 0x7FFF),
        (-0x8000, -0x8000), (0x7FFF, -0x8000), (100, -200), (-300, 400),
        (0x0100, 0x0100), (0x00FF, 0x00FF), (-128, 127), (1000, -1000),
    ]
    _run(mixed, "16 distinct pairs")

    # random
    _random.seed(42)
    rand_pairs = [
        (_random.randint(-0x8000, 0x7FFF), _random.randint(-0x8000, 0x7FFF))
        for _ in range(16)
    ]
    _run(rand_pairs, "random seed 42")

    print("All tests passed!")


if __name__ == "__main__":
    test()
    sys.exit(main())
