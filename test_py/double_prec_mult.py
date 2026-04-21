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
"""

import sys

from bitstring import BitArray
from util import Machine


def mul_u8x8(vm: Machine, ra: str, rb: str) -> None:
    """
    Unsigned 8x8 -> 16-bit multiply via shift-and-add.
    Result placed in r5 (high byte) and r6 (low byte).
    Clobbers r5, r6, r14, r15, r16.
    Requires r8 = 0x00 and r9 = 0x01 as constants.
    """
    vm.set_reg("r5", BitArray(uint=0, length=8))    # acc_hi = 0
    vm.set_reg("r6", BitArray(uint=0, length=8))    # acc_lo = 0
    vm.set_reg("r14", BitArray(uint=0, length=8))   # shf_hi = 0
    vm.set_reg("r15", vm.get_reg(ra))               # shf_lo = ra

    for i in range(8):
        # Isolate bit i of multiplier into r16 (0x00 or 0x01)
        vm.set_reg("r16", vm.get_reg(rb))           # r16 = rb
        if i > 0:
            vm.rsh("r16", i)                        # r16 >>= i  (logical)
        vm.and_reg("r16", "r16", "r9")              # r16 &= 1

        # If bit i is set, accumulate shf_hi:shf_lo into acc_hi:acc_lo
        vm.ucmp("r16", "r8")
        if vm.zero_flag.uint == 0:                  # bit is 1
            vm.add("r6", "r6", "r15")              # acc_lo += shf_lo
            carry = vm.carry_flag.uint
            vm.add("r5", "r5", "r14")              # acc_hi += shf_hi
            if carry:
                vm.add("r5", "r5", "r9")           # acc_hi += carry

        # Left-shift shf_hi:shf_lo by 1 (skip after last bit)
        if i < 7:
            vm.set_reg("r16", vm.get_reg("r15"))   # r16 = shf_lo
            vm.rsh("r16", 7)                       # r16 = MSB of shf_lo (0 or 1)
            vm.lsh("r14", 1)                       # shf_hi <<= 1
            vm.lsh("r15", 1)                       # shf_lo <<= 1
            vm.add("r14", "r14", "r16")            # shf_hi |= carry-in from shf_lo


def main() -> int:
    vm = Machine()

    vm.set_reg("r8", BitArray(uint=0x00, length=8))  # r8 = constant 0x00
    vm.set_reg("r9", BitArray(uint=0x01, length=8))  # r9 = constant 0x01

    for n in range(16):
        base = 4 * n

        # Load operand A: r1 = A_hi (signed byte), r2 = A_lo (unsigned byte)
        vm.get_mem("r1", base + 0)
        vm.get_mem("r2", base + 1)

        # Load operand B: r3 = B_hi (signed byte), r4 = B_lo (unsigned byte)
        vm.get_mem("r3", base + 2)
        vm.get_mem("r4", base + 3)

        # Extract sign bits via AND with 0x80 mask
        # r5 = 0x80 if A is negative, else 0x00
        # r6 = 0x80 if B is negative, else 0x00
        vm.set_reg("r16", BitArray(uint=0x80, length=8))  # sign bit mask
        vm.and_reg("r5", "r1", "r16")               # r5 = sign of A
        vm.and_reg("r6", "r3", "r16")               # r6 = sign of B

        # r7 = result sign: 0x80 if product is negative, else 0x00
        vm.xor("r7", "r5", "r6")                   # r7 = sign_A XOR sign_B

        # Negate A if negative (two's complement: invert all bits then add 1)
        vm.ucmp("r5", "r8")
        if vm.zero_flag.uint == 0:                  # A is negative
            vm.invert_reg("r1")
            vm.invert_reg("r2")
            vm.add("r2", "r2", "r9")
            if vm.carry_flag.uint == 1:
                vm.add("r1", "r1", "r9")

        # Negate B if negative
        vm.ucmp("r6", "r8")
        if vm.zero_flag.uint == 0:                  # B is negative
            vm.invert_reg("r3")
            vm.invert_reg("r4")
            vm.add("r4", "r4", "r9")
            if vm.carry_flag.uint == 1:
                vm.add("r3", "r3", "r9")

        # Now r1:r2 = |A| and r3:r4 = |B| (both unsigned 16-bit magnitudes).
        # Compute 32-bit product into r10:r11:r12:r13 using four 8x8 partial products:
        #
        #   A * B = A_hi*B_hi * 2^16 + (A_hi*B_lo + A_lo*B_hi) * 2^8 + A_lo*B_lo
        #           contributes to [r10:r11]   [r11:r12]                  [r12:r13]

        # P_ll = A_lo * B_lo  (r2 * r4)  ->  r5:r6
        mul_u8x8(vm, "r2", "r4")
        vm.set_reg("r10", BitArray(uint=0, length=8))
        vm.set_reg("r11", BitArray(uint=0, length=8))
        vm.set_reg("r12", vm.get_reg("r5"))         # prod[2] = P_ll_hi
        vm.set_reg("r13", vm.get_reg("r6"))         # prod[3] = P_ll_lo

        # P_hl = A_hi * B_lo  (r1 * r4)  ->  r5:r6; add into r11:r12
        mul_u8x8(vm, "r1", "r4")
        vm.add("r12", "r12", "r6")
        c_lo = vm.carry_flag.uint
        vm.add("r11", "r11", "r5")
        c_hi = vm.carry_flag.uint
        if c_lo:
            vm.add("r11", "r11", "r9")
            if vm.carry_flag.uint:
                c_hi = 1
        if c_hi:
            vm.add("r10", "r10", "r9")

        # P_lh = A_lo * B_hi  (r2 * r3)  ->  r5:r6; add into r11:r12
        mul_u8x8(vm, "r2", "r3")
        vm.add("r12", "r12", "r6")
        c_lo = vm.carry_flag.uint
        vm.add("r11", "r11", "r5")
        c_hi = vm.carry_flag.uint
        if c_lo:
            vm.add("r11", "r11", "r9")
            if vm.carry_flag.uint:
                c_hi = 1
        if c_hi:
            vm.add("r10", "r10", "r9")

        # P_hh = A_hi * B_hi  (r1 * r3)  ->  r5:r6; add into r10:r11
        mul_u8x8(vm, "r1", "r3")
        vm.add("r11", "r11", "r6")
        c_lo = vm.carry_flag.uint
        vm.add("r10", "r10", "r5")
        if c_lo:
            vm.add("r10", "r10", "r9")

        # Negate the 32-bit result if the product sign is negative
        vm.ucmp("r7", "r8")
        if vm.zero_flag.uint == 0:                  # product is negative
            vm.invert_reg("r10")
            vm.invert_reg("r11")
            vm.invert_reg("r12")
            vm.invert_reg("r13")
            vm.add("r13", "r13", "r9")
            if vm.carry_flag.uint == 1:
                vm.add("r12", "r12", "r9")
                if vm.carry_flag.uint == 1:
                    vm.add("r11", "r11", "r9")
                    if vm.carry_flag.uint == 1:
                        vm.add("r10", "r10", "r9")

        # Write 32-bit product to output memory at offset 64+4N
        vm.set_mem(64 + 4 * n + 0, "r10")
        vm.set_mem(64 + 4 * n + 1, "r11")
        vm.set_mem(64 + 4 * n + 2, "r12")
        vm.set_mem(64 + 4 * n + 3, "r13")

    # Verify results against Python's native multiplication
    all_ok = True
    for n in range(16):
        base = 4 * n
        a = vm.mem[base + 0].int * 256 + vm.mem[base + 1].uint
        b = vm.mem[base + 2].int * 256 + vm.mem[base + 3].uint
        expected = a * b

        rb = 64 + 4 * n
        raw = ((vm.mem[rb].uint << 24) | (vm.mem[rb + 1].uint << 16)
               | (vm.mem[rb + 2].uint << 8) | vm.mem[rb + 3].uint)
        actual = raw if raw < (1 << 31) else raw - (1 << 32)

        status = "OK" if expected == actual else f"FAIL (expected {expected})"
        print(f"A[{n:2d}]={a:7d} * B[{n:2d}]={b:7d} = {actual:12d}  {status}")
        if expected != actual:
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
