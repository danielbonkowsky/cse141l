"""
Write a program to find the absolute values of the least and greatest
arithmetic difference among all pairs of incoming values from Program 2.
Assume again that all values are two's complement (“signed”) 16-bit integers.
The array of integers starts at location 0. Write the absolute value of the
minimum difference in locations 66-67 and the maximum in 68-69. Format:
mem[66] = MSB of smallest absolute value difference among pairs;
mem[67] = LSB.
mem[68] = MSB of largest absolute value difference among
pairs, mem[69] = LSB.
"""

import sys

from bitstring import BitArray
from util import Machine


def positive_op_dist(vm: Machine) -> None:
    """returns the distance between two positive ops. assumes they are stored as
        mem[128] = msb1
        mem[129] = lsb1
        mem[130] = msb2
        mem[131] = lsb2
    and returns the result as
        mem[128] = dist msb
        mem[129] = dist lsb
    preserves r0, r1
    """
    # r2 <- MSB2 addr
    vm.ldi_I(BitArray(uint=130, length=8))
    vm.sto_R("r2")

    # r2 <- MSB2
    vm.ld_R("r2")
    vm.sto_R("r2")

    # r3 <- MSB1 addr
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r3")

    # acc <- MSB1
    vm.ld_R("r3")

    vm.cmp_R("r2")
    # if msb1 < msb2
    if vm.sign_flag[0]:
        # r2 <- msb2; r3 <- lsb2; r4 <- msb1; r5 <- lsb1
        # r4 <- msb1
        vm.sto_R("r4")

        # r3 <- lsb2 addr
        vm.ldi_I(BitArray(uint=131, length=8))
        vm.sto_R("r3")

        # r3 <- lsb2
        vm.ld_R("r3")
        vm.sto_R("r3")

        # r5 <- lsb1 addr
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r5")

        # r5 <- lsb1
        vm.ld_R("r5")
        vm.sto_R("r5")

    # if msb1 > msb2 (not less than or equal)
    elif not vm.zero_flag[0]:
        # r2 <- msb1; r3 <- lsb1; r4 <- msb2; r5 <- lsb2
        # r2 <- msb1
        vm.sto_R("r2")

        # r3 <- lsb1 addr
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r3")

        # r3 <- lsb1
        vm.ld_R("r3")
        vm.sto_R("r3")

        # r4 <- msb2 addr
        vm.ldi_I(BitArray(uint=130, length=8))
        vm.sto_R("r4")

        # r4 <- msb2
        vm.ld_R("r4")
        vm.sto_R("r4")

        # r5 <- lsb2 addr
        vm.ldi_I(BitArray(uint=131, length=8))
        vm.sto_R("r5")

        # r5 <- lsb2
        vm.ld_R("r5")
        vm.sto_R("r5")

    # now we need to compare lsbs
    else:
        # r2 <- lsb2 addr
        vm.ldi_I(BitArray(uint=131, length=8))
        vm.sto_R("r2")

        # r2 <- lsb2
        vm.ld_R("r2")
        vm.sto_R("r2")

        # r3 <- lsb1 addr
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r3")

        # acc <- lsb1
        vm.ld_R("r3")

        vm.cmp_R("r2")
        # if lsb1 < lsb2 (and msbs are guaranteed equal)
        if vm.carry_flag[0]:
            # r2 <- msb2; r3 <- lsb2; r4 <- msb1; r5 <- lsb1
            # r5 <- lsb1
            vm.sto_R("r5")

            # r3 <- lsb2
            vm.mov_R("r2")
            vm.sto_R("r3")

            # r2 <- msb2 addr
            vm.ldi_I(BitArray(uint=130, length=8))
            vm.sto_R("r2")

            # r2 <- msb2
            vm.ld_R("r2")
            vm.sto_R("r2")

            # r4 <- msb1 addr
            vm.ldi_I(BitArray(uint=128, length=8))
            vm.sto_R("r4")

            # r4 <- msb1
            vm.ld_R("r4")
            vm.sto_R("r4")

        # at this point, we know op1 >= op2
        else:
            # r2 <- msb1; r3 <- lsb1; r4 <- msb2; r5 <- lsb2
            # r3 <- lsb1
            vm.sto_R("r3")

            # r5 <- lsb2
            vm.mov_R("r2")
            vm.sto_R("r5")

            # r2 <- msb1 addr
            vm.ldi_I(BitArray(uint=128, length=8))
            vm.sto_R("r2")

            # r2 <- msb1
            vm.ld_R("r2")
            vm.sto_R("r2")

            # r4 <- msb2 addr
            vm.ldi_I(BitArray(uint=130, length=8))
            vm.sto_R("r4")

            # r4 <- msb2
            vm.ld_R("r4")
            vm.sto_R("r4")

    # POSTCONDITION: [r2 r3] >= [r4 r5]

    # now we negate [r4 r5]
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

    # add [r2 r3] + [r4 r5]
    vm.mov_R("r3")
    vm.add_R("r5")
    vm.sto_R("r3")
    vm.mov_R("r2")
    if vm.carry_flag[0]:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.add_R("r4")
    vm.sto_R("r2")

    # POSTCONDITION [r2 r3] is the arithmetic distance between op1 and op2

    # store in memory
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r4")
    vm.mov_R("r2")
    vm.st_R("r4")
    vm.ldi_I(BitArray(uint=129, length=8))
    vm.sto_R("r4")
    vm.mov_R("r3")
    vm.st_R("r4")


def negative_op_dist(vm: Machine) -> None:
    """returns the distance between two negative ops. assumes they are stored as
        mem[128] = msb1
        mem[129] = lsb1
        mem[130] = msb2
        mem[131] = lsb2
    and returns the result as
        mem[128] = dist msb
        mem[129] = dist lsb
    preserves r0, r1
    """
    # make op1 positive
    # r2 <- msb1
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r2")
    vm.ld_R("r2")
    vm.sto_R("r2")

    # acc <- lsb1
    vm.ldi_I(BitArray(uint=129, length=8))
    vm.sto_R("r3")
    vm.ld_R("r3")

    # negate
    vm.inv_R()
    vm.sto_R("r3")
    vm.mov_R("r2")
    vm.inv_R()
    vm.sto_R("r2")
    vm.mov_R("r3")
    vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r3")
    if vm.carry_flag[0]:
        vm.mov_R("r2")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r2")

    # postcondition: [r2 r3] is negated [mem[128] mem[129]]
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r4")
    vm.mov_R("r2")
    vm.st_R("r4")
    vm.ldi_I(BitArray(uint=129, length=8))
    vm.sto_R("r4")
    vm.mov_R("r3")
    vm.st_R("r4")

    # make op2 positive
    # r2 <- msb2
    vm.ldi_I(BitArray(uint=130, length=8))
    vm.sto_R("r2")
    vm.ld_R("r2")
    vm.sto_R("r2")

    # acc <- lsb2
    vm.ldi_I(BitArray(uint=131, length=8))
    vm.sto_R("r3")
    vm.ld_R("r3")

    # negate
    vm.inv_R()
    vm.sto_R("r3")
    vm.mov_R("r2")
    vm.inv_R()
    vm.sto_R("r2")
    vm.mov_R("r3")
    vm.addi_I(BitArray(uint=1, length=8))
    vm.sto_R("r3")
    if vm.carry_flag[0]:
        vm.mov_R("r2")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r2")

    # postcondition: [r2 r3] is negated [mem[130] mem[131]]
    vm.ldi_I(BitArray(uint=130, length=8))
    vm.sto_R("r4")
    vm.mov_R("r2")
    vm.st_R("r4")
    vm.ldi_I(BitArray(uint=131, length=8))
    vm.sto_R("r4")
    vm.mov_R("r3")
    vm.st_R("r4")

    positive_op_dist(vm)


def diff_sign_dist(vm: Machine) -> None:
    """returns the distance between two ops of different signs. assumes they are
    stored as
        mem[128] = msb1
        mem[129] = lsb1
        mem[130] = msb2
        mem[131] = lsb2
    and returns the result as
        mem[128] = dist msb
        mem[129] = dist lsb
    preserves r0, r1
    """
    # acc <- msb1
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r2")
    vm.ld_R("r2")

    # is op1 negative?
    vm.lsh_I(BitArray(uint=1, length=8))
    if vm.carry_flag[0]:
        # r2 <- msb1
        vm.ldi_I(BitArray(uint=128, length=8))
        vm.sto_R("r2")
        vm.ld_R("r2")
        vm.sto_R("r2")

        # acc <- lsb1
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r3")
        vm.ld_R("r3")

        # negate
        vm.inv_R()
        vm.sto_R("r3")
        vm.mov_R("r2")
        vm.inv_R()
        vm.sto_R("r2")
        vm.mov_R("r3")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r3")
        if vm.carry_flag[0]:
            vm.mov_R("r2")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")

        # r4 <- msb2
        vm.ldi_I(BitArray(uint=130, length=8))
        vm.sto_R("r4")
        vm.ld_R("r4")
        vm.sto_R("r4")

        # r5 <- lsb2
        vm.ldi_I(BitArray(uint=131, length=8))
        vm.sto_R("r5")
        vm.ld_R("r5")
        vm.sto_R("r5")
    else:
        # r2 <- msb2
        vm.ldi_I(BitArray(uint=130, length=8))
        vm.sto_R("r2")
        vm.ld_R("r2")
        vm.sto_R("r2")

        # acc <- lsb2
        vm.ldi_I(BitArray(uint=131, length=8))
        vm.sto_R("r3")
        vm.ld_R("r3")

        # negate
        vm.inv_R()
        vm.sto_R("r3")
        vm.mov_R("r2")
        vm.inv_R()
        vm.sto_R("r2")
        vm.mov_R("r3")
        vm.addi_I(BitArray(uint=1, length=8))
        vm.sto_R("r3")
        if vm.carry_flag[0]:
            vm.mov_R("r2")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")

        # r4 <- msb1
        vm.ldi_I(BitArray(uint=128, length=8))
        vm.sto_R("r4")
        vm.ld_R("r4")
        vm.sto_R("r4")

        # r5 <- lsb1
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r5")
        vm.ld_R("r5")
        vm.sto_R("r5")

    # postcondition: [r2 r3] [r4 r5] are the ops to be added
    vm.mov_R("r3")
    vm.add_R("r5")
    vm.sto_R("r3")
    vm.mov_R("r2")
    if vm.carry_flag[0]:
        vm.addi_I(BitArray(uint=1, length=8))
    vm.add_R("r4")
    vm.sto_R("r2")

    # store in memory
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r4")
    vm.mov_R("r2")
    vm.st_R("r4")
    vm.ldi_I(BitArray(uint=129, length=8))
    vm.sto_R("r4")
    vm.mov_R("r3")
    vm.st_R("r4")


def update_min_max(vm: Machine) -> None:
    """update the minimum and maximum distance values. assumes distances are
    stored as
    mem[128] = curr msb
    mem[129] = curr lsb
    mem[66] = min msb
    mem[67] = min lsb
    mem[68] = max msb
    mem[69] = max lsb
    """
    # update min
    # r2 <- min msb
    vm.ldi_I(BitArray(uint=66, length=8))
    vm.sto_R("r2")
    vm.ld_R("r2")
    vm.sto_R("r2")

    # acc <- curr msb
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r3")
    vm.ld_R("r3")

    # compare msbs
    vm.cmp_R("r2")
    if vm.carry_flag[0]:
        # update min value
        # r2 <- curr msb
        vm.ldi_I(BitArray(uint=128, length=8))
        vm.sto_R("r2")
        vm.ld_R("r2")
        vm.sto_R("r2")
        # r3 <- curr lsb
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r3")
        vm.ld_R("r3")
        vm.sto_R("r3")
        # update min msb
        vm.ldi_I(BitArray(uint=66, length=8))
        vm.sto_R("r4")
        vm.mov_R("r2")
        vm.st_R("r4")
        # update min lsb
        vm.ldi_I(BitArray(uint=67, length=8))
        vm.sto_R("r4")
        vm.mov_R("r3")
        vm.st_R("r4")
    elif vm.zero_flag[0]:
        # compare lsbs
        # r2 <- min lsb
        vm.ldi_I(BitArray(uint=67, length=8))
        vm.sto_R("r2")
        vm.ld_R("r2")
        vm.sto_R("r2")

        # acc <- curr lsb
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r3")
        vm.ld_R("r3")

        # compare lsbs
        vm.cmp_R("r2")
        if vm.carry_flag[0]:
            # update min value
            # r2 <- curr msb
            vm.ldi_I(BitArray(uint=128, length=8))
            vm.sto_R("r2")
            vm.ld_R("r2")
            vm.sto_R("r2")
            # r3 <- curr lsb
            vm.ldi_I(BitArray(uint=129, length=8))
            vm.sto_R("r3")
            vm.ld_R("r3")
            vm.sto_R("r3")
            # update min msb
            vm.ldi_I(BitArray(uint=66, length=8))
            vm.sto_R("r4")
            vm.mov_R("r2")
            vm.st_R("r4")
            # update min lsb
            vm.ldi_I(BitArray(uint=67, length=8))
            vm.sto_R("r4")
            vm.mov_R("r3")
            vm.st_R("r4")

    # update max
    # r2 <- curr msb
    vm.ldi_I(BitArray(uint=128, length=8))
    vm.sto_R("r2")
    vm.ld_R("r2")
    vm.sto_R("r2")

    # acc <- max msb
    vm.ldi_I(BitArray(uint=68, length=8))
    vm.sto_R("r3")
    vm.ld_R("r3")

    # compare msbs
    vm.cmp_R("r2")
    if vm.carry_flag[0]:
        # update max value
        # r2 <- curr msb
        vm.ldi_I(BitArray(uint=128, length=8))
        vm.sto_R("r2")
        vm.ld_R("r2")
        vm.sto_R("r2")
        # r3 <- curr lsb
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r3")
        vm.ld_R("r3")
        vm.sto_R("r3")
        # update max msb
        vm.ldi_I(BitArray(uint=68, length=8))
        vm.sto_R("r4")
        vm.mov_R("r2")
        vm.st_R("r4")
        # update min lsb
        vm.ldi_I(BitArray(uint=69, length=8))
        vm.sto_R("r4")
        vm.mov_R("r3")
        vm.st_R("r4")
    elif vm.zero_flag[0]:
        # compare lsbs
        # r2 <- curr lsb
        vm.ldi_I(BitArray(uint=129, length=8))
        vm.sto_R("r2")
        vm.ld_R("r2")
        vm.sto_R("r2")

        # acc <- max lsb
        vm.ldi_I(BitArray(uint=69, length=8))
        vm.sto_R("r3")
        vm.ld_R("r3")

        # compare lsbs
        vm.cmp_R("r2")
        if vm.carry_flag[0]:
            # update min value
            # r2 <- curr msb
            vm.ldi_I(BitArray(uint=128, length=8))
            vm.sto_R("r2")
            vm.ld_R("r2")
            vm.sto_R("r2")
            # r3 <- curr lsb
            vm.ldi_I(BitArray(uint=129, length=8))
            vm.sto_R("r3")
            vm.ld_R("r3")
            vm.sto_R("r3")
            # update min msb
            vm.ldi_I(BitArray(uint=68, length=8))
            vm.sto_R("r4")
            vm.mov_R("r2")
            vm.st_R("r4")
            # update min lsb
            vm.ldi_I(BitArray(uint=69, length=8))
            vm.sto_R("r4")
            vm.mov_R("r3")
            vm.st_R("r4")


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
    # intialize min and max values
    # min msb
    vm.ldi_I(BitArray(uint=66, length=8))
    vm.sto_R("r0")
    vm.ldi_I(BitArray(uint=255, length=8))
    vm.st_R("r0")
    # min lsb
    vm.ldi_I(BitArray(uint=67, length=8))
    vm.sto_R("r0")
    vm.ldi_I(BitArray(uint=255, length=8))
    vm.st_R("r0")
    # max msb
    vm.ldi_I(BitArray(uint=68, length=8))
    vm.sto_R("r0")
    vm.ldi_I(BitArray(uint=0, length=8))
    vm.st_R("r0")
    # max lsb
    vm.ldi_I(BitArray(uint=69, length=8))
    vm.sto_R("r0")
    vm.ldi_I(BitArray(uint=0, length=8))
    vm.st_R("r0")

    for i in range(32):
        for j in range(i + 1, 32):
            # r0 and r1 reserved for i, j
            vm.ldi_I(BitArray(uint=i, length=8))
            vm.sto_R("r0")
            vm.ldi_I(BitArray(uint=j, length=8))
            vm.sto_R("r1")

            # store vals in memory
            # mem[128] <- msb1
            vm.mov_R("r0")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")
            vm.ld_R("r2")
            vm.sto_R("r2")
            vm.ldi_I(BitArray(uint=128, length=8))
            vm.sto_R("r3")
            vm.mov_R("r2")
            vm.st_R("r3")
            # mem[129] <- lsb1
            vm.mov_R("r0")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")
            vm.ld_R("r2")
            vm.sto_R("r2")
            vm.ldi_I(BitArray(uint=129, length=8))
            vm.sto_R("r3")
            vm.mov_R("r2")
            vm.st_R("r3")
            # mem[130] <- msb2
            vm.mov_R("r1")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")
            vm.ld_R("r2")
            vm.sto_R("r2")
            vm.ldi_I(BitArray(uint=130, length=8))
            vm.sto_R("r3")
            vm.mov_R("r2")
            vm.st_R("r3")
            # mem[131] <- lsb2
            vm.mov_R("r1")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")
            vm.ld_R("r2")
            vm.sto_R("r2")
            vm.ldi_I(BitArray(uint=131, length=8))
            vm.sto_R("r3")
            vm.mov_R("r2")
            vm.st_R("r3")

            # acc <- msb1
            vm.mov_R("r0")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.sto_R("r2")
            vm.ld_R("r2")
            # is it negative?
            vm.lsh_I(BitArray(uint=1, length=8))
            if vm.carry_flag[0]:
                # acc <- msb2
                vm.mov_R("r1")
                vm.lsh_I(BitArray(uint=1, length=8))
                vm.sto_R("r2")
                vm.ld_R("r2")
                # is it negative?
                vm.lsh_I(BitArray(uint=1, length=8))
                if vm.carry_flag[0]:
                    negative_op_dist(vm)
                else:
                    diff_sign_dist(vm)
            else:
                # acc <- msb2
                vm.mov_R("r1")
                vm.lsh_I(BitArray(uint=1, length=8))
                vm.sto_R("r2")
                vm.ld_R("r2")
                # is it negative?
                vm.lsh_I(BitArray(uint=1, length=8))
                if vm.carry_flag[0]:
                    diff_sign_dist(vm)
                else:
                    positive_op_dist(vm)

            update_min_max(vm)

    return 0


if __name__ == "__main__":
    test()
    sys.exit(main())
