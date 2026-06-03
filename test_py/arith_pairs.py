"""
Write a program to find the absolute values of the least and greatest
arithmetic difference among all pairs of incoming values from Program 2.
Assume again that all values are two's complement ("signed") 16-bit integers.
The array of integers starts at location 0. Write the absolute value of the
minimum difference in locations 66-67 and the maximum in 68-69. Format:
mem[66] = MSB of smallest absolute value difference among pairs;
mem[67] = LSB.
mem[68] = MSB of largest absolute value difference among
pairs, mem[69] = LSB.

Register allocation (shared across main and all helper functions):
    r0  = i              (outer loop index)
    r1  = j              (inner loop index)
    r2  = msb_a         (MSB of operand A for this pair)
    r3  = lsb_a         (LSB of operand A)
    r4  = msb_b         (MSB of operand B)
    r5  = lsb_b         (LSB of operand B)
    r6  = addr / scratch
    r7  = addr / scratch
    r8  = min_msb        (running minimum distance, MSB)
    r9  = min_lsb        (running minimum distance, LSB)
    r10 = max_msb        (running maximum distance, MSB)
    r11 = max_lsb        (running maximum distance, LSB)

Helper function contracts:
    positive_op_dist: [r2,r3] and [r4,r5] are both non-negative.
                      Writes |A - B| to [r2,r3]. Uses r6, r7 as scratch.
    negative_op_dist: [r2,r3] and [r4,r5] are both negative.
                      Writes |A - B| to [r2,r3]. Uses r6, r7 as scratch.
    diff_sign_dist:   [r2,r3] and [r4,r5] have opposite signs.
                      Writes |A - B| to [r2,r3].
    update_min_max:   [r2,r3] = current distance.
                      Compares against r8-r11 and updates them in place.
"""

import sys

from bitstring import BitArray
from util import Machine


def positive_op_dist(vm: Machine) -> None:
    """[r2,r3] and [r4,r5] are non-negative. Writes |A - B| to [r2,r3].

    Sorts so [r2,r3] >= [r4,r5], negates [r4,r5], then adds.
    Uses r6, r7 as swap scratch.
    """
    # sort: ensure [r2,r3] >= [r4,r5]
    vm.mov_R("r2")
    vm.cmp_R("r4")
    if vm.sign_flag[0]:
        # msb_a < msb_b → swap both pairs
        vm.mov_R("r2"); vm.sto_R("r6")
        vm.mov_R("r4"); vm.sto_R("r2")
        vm.mov_R("r6"); vm.sto_R("r4")
        vm.mov_R("r3"); vm.sto_R("r7")
        vm.mov_R("r5"); vm.sto_R("r3")
        vm.mov_R("r7"); vm.sto_R("r5")
    elif vm.zero_flag[0]:
        # msbs equal → compare lsbs (unsigned)
        vm.mov_R("r3")
        vm.cmp_R("r5")
        if vm.carry_flag[0]:
            # lsb_a < lsb_b → swap both pairs
            vm.mov_R("r2"); vm.sto_R("r6")
            vm.mov_R("r4"); vm.sto_R("r2")
            vm.mov_R("r6"); vm.sto_R("r4")
            vm.mov_R("r3"); vm.sto_R("r7")
            vm.mov_R("r5"); vm.sto_R("r3")
            vm.mov_R("r7"); vm.sto_R("r5")

    # postcondition: [r2,r3] >= [r4,r5]

    # negate [r4,r5]
    vm.mov_R("r4")
    vm.inv_R()
    vm.sto_R("r4")
    vm.mov_R("r5")
    vm.inv_R()
    vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r5")
    if vm.carry_flag[0]:
        vm.mov_R("r4")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r4")

    # [r2,r3] + negated [r4,r5] = [r2,r3] - original [r4,r5]
    vm.mov_R("r3")
    vm.add_R("r5")
    vm.sto_R("r3")
    vm.mov_R("r2")
    if vm.carry_flag[0]:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.add_R("r4")
    vm.sto_R("r2")


def negative_op_dist(vm: Machine) -> None:
    """[r2,r3] and [r4,r5] are both negative. Writes |A - B| to [r2,r3].

    Negates both operands in place, then delegates to positive_op_dist.
    """
    # negate [r2,r3]
    vm.mov_R("r2")
    vm.inv_R()
    vm.sto_R("r2")
    vm.mov_R("r3")
    vm.inv_R()
    vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r3")
    if vm.carry_flag[0]:
        vm.mov_R("r2")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r2")

    # negate [r4,r5]
    vm.mov_R("r4")
    vm.inv_R()
    vm.sto_R("r4")
    vm.mov_R("r5")
    vm.inv_R()
    vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r5")
    if vm.carry_flag[0]:
        vm.mov_R("r4")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r4")

    positive_op_dist(vm)


def diff_sign_dist(vm: Machine) -> None:
    """[r2,r3] and [r4,r5] have opposite signs. Writes |A - B| to [r2,r3].

    Negates the negative operand, then adds the two magnitudes.
    """
    # shift MSB left; carry = sign bit of op A
    vm.mov_R("r2")
    vm.shf_I(BitArray(int=1, length=8))
    if vm.carry_flag[0]:
        # op A is negative → negate [r2,r3]
        vm.mov_R("r2")
        vm.inv_R()
        vm.sto_R("r2")
        vm.mov_R("r3")
        vm.inv_R()
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r3")
        if vm.carry_flag[0]:
            vm.mov_R("r2")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")
    else:
        # op B is negative → negate [r4,r5]
        vm.mov_R("r4")
        vm.inv_R()
        vm.sto_R("r4")
        vm.mov_R("r5")
        vm.inv_R()
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r5")
        if vm.carry_flag[0]:
            vm.mov_R("r4")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r4")

    # add the two (now positive) magnitudes
    vm.mov_R("r3")
    vm.add_R("r5")
    vm.sto_R("r3")
    vm.mov_R("r2")
    if vm.carry_flag[0]:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.add_R("r4")
    vm.sto_R("r2")


def update_min_max(vm: Machine) -> None:
    """[r2,r3] = current distance. Updates r8-r11 (min/max) in place."""
    # update min: if curr < min, min = curr
    vm.mov_R("r2")
    vm.cmp_R("r8")
    if vm.carry_flag[0]:
        # curr_msb < min_msb
        vm.mov_R("r2"); vm.sto_R("r8")
        vm.mov_R("r3"); vm.sto_R("r9")
    elif vm.zero_flag[0]:
        # msbs equal → compare lsbs (unsigned)
        vm.mov_R("r3")
        vm.cmp_R("r9")
        if vm.carry_flag[0]:
            vm.mov_R("r2"); vm.sto_R("r8")
            vm.mov_R("r3"); vm.sto_R("r9")

    # update max: if curr > max, max = curr
    vm.mov_R("r10")
    vm.cmp_R("r2")
    if vm.carry_flag[0]:
        # max_msb < curr_msb
        vm.mov_R("r2"); vm.sto_R("r10")
        vm.mov_R("r3"); vm.sto_R("r11")
    elif vm.zero_flag[0]:
        # msbs equal → compare lsbs (unsigned)
        vm.mov_R("r11")
        vm.cmp_R("r3")
        if vm.carry_flag[0]:
            vm.mov_R("r2"); vm.sto_R("r10")
            vm.mov_R("r3"); vm.sto_R("r11")


def test() -> None:
    import random as _random

    def _run(values: list[int], label: str) -> None:
        vm = Machine()
        for idx, v in enumerate(values):
            v_u = v & 0xFFFF
            vm.mem[idx * 2] = BitArray(uint=(v_u >> 8) & 0xFF, length=8)
            vm.mem[idx * 2 + 1] = BitArray(uint=v_u & 0xFF, length=8)
        main(vm)
        diffs = [
            abs(values[i] - values[j]) for i in range(32) for j in range(i + 1, 32)
        ]
        got_min = (vm.mem[66].uint << 8) | vm.mem[67].uint
        got_max = (vm.mem[68].uint << 8) | vm.mem[69].uint
        assert got_min == min(diffs), (
            f"{label}: min wrong (got {got_min}, expected {min(diffs)})"
        )
        assert got_max == max(diffs), (
            f"{label}: max wrong (got {got_max}, expected {max(diffs)})"
        )

    _run([0] * 32, "all zeros")
    _run([100] * 32, "all same")
    _run(list(range(32)), "sequential positive")
    _run(list(range(-32, 0)), "sequential negative")
    _run([0x7FFF, -0x8000] + [0] * 30, "extremes with zeros")
    _run([0x7FFF] * 16 + [-0x8000] * 16, "half max half min")
    _random.seed(42)
    _run([_random.randint(-0x8000, 0x7FFF) for _ in range(32)], "random seed 42")
    print("All tests passed!")


def main(vm: Machine | None = None) -> int:
    if vm is None:
        vm = Machine()

    # r8,r9 = min dist (init to 0xFFFF, the largest possible 16-bit value)
    vm.ldi_I(BitArray(uint=255, length=8))
    vm.sto_R("r8")
    vm.sto_R("r9")

    # r10,r11 = max dist (init to 0x0000)
    vm.ldi_I(BitArray(uint=0, length=8))
    vm.sto_R("r10")
    vm.sto_R("r11")

    for i in range(32):
        for j in range(i + 1, 32):
            vm.ldi_I(BitArray(uint=i, length=8))
            vm.sto_R("r0")
            vm.ldi_I(BitArray(uint=j, length=8))
            vm.sto_R("r1")

            # load op A: r2 = msb, r3 = lsb  from mem[2*i], mem[2*i+1]
            vm.mov_R("r0")
            vm.shf_I(BitArray(int=1, length=8))
            vm.sto_R("r6")                          # r6 = 2*i
            vm.ld_R("r6")
            vm.sto_R("r2")                          # r2 = msb_a
            vm.mov_R("r6")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r7")                          # r7 = 2*i+1
            vm.ld_R("r7")
            vm.sto_R("r3")                          # r3 = lsb_a

            # load op B: r4 = msb, r5 = lsb  from mem[2*j], mem[2*j+1]
            vm.mov_R("r1")
            vm.shf_I(BitArray(int=1, length=8))
            vm.sto_R("r6")                          # r6 = 2*j
            vm.ld_R("r6")
            vm.sto_R("r4")                          # r4 = msb_b
            vm.mov_R("r6")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r7")                          # r7 = 2*j+1
            vm.ld_R("r7")
            vm.sto_R("r5")                          # r5 = lsb_b

            # dispatch on sign combination (shift MSB left; carry = sign bit)
            vm.mov_R("r2")
            vm.shf_I(BitArray(int=1, length=8))
            if vm.carry_flag[0]:                    # op A is negative
                vm.mov_R("r4")
                vm.shf_I(BitArray(int=1, length=8))
                if vm.carry_flag[0]:                # op B also negative
                    negative_op_dist(vm)
                else:
                    diff_sign_dist(vm)
            else:                                   # op A is positive
                vm.mov_R("r4")
                vm.shf_I(BitArray(int=1, length=8))
                if vm.carry_flag[0]:                # op B is negative
                    diff_sign_dist(vm)
                else:
                    positive_op_dist(vm)

            update_min_max(vm)

    # write min to mem[66-67], max to mem[68-69]
    vm.ldi_I(BitArray(uint=66, length=8))
    vm.sto_R("r6")
    vm.mov_R("r8")
    vm.st_R("r6")

    vm.ldi_I(BitArray(uint=67, length=8))
    vm.sto_R("r6")
    vm.mov_R("r9")
    vm.st_R("r6")

    vm.ldi_I(BitArray(uint=68, length=8))
    vm.sto_R("r6")
    vm.mov_R("r10")
    vm.st_R("r6")

    vm.ldi_I(BitArray(uint=69, length=8))
    vm.sto_R("r6")
    vm.mov_R("r11")
    vm.st_R("r6")

    return 0


if __name__ == "__main__":
    test()
    sys.exit(main())
