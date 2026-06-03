"""
Write a program to find the least and greatest Hamming distances among all
pairs of values in an array of 32 two-byte half-words. Assume all values are
signed 16-bit ("half-word") integers. The array of integers runs from data
memory location 0 to 63. Even-numbered addresses are MSBs, following odd
addresses are LSBs, e.g. a concatenation of addresses 0 and 1 forms a 16-bit
two's complement half-word. Write the minimum distance in location 64 and the
maximum in 65.

Register allocation:
    r0  = i              (outer loop index)
    r1  = j              (inner loop index)
    r2  = min_dist
    r3  = max_dist
    r4  = curr_dist      (this pair)
    r5  = addr_msb1      (2*i)
    r6  = addr_lsb1      (2*i + 1)
    r7  = addr_msb2      (2*j)
    r8  = addr_lsb2      (2*j + 1)
    r9  = xor_msb        (MSB1 XOR MSB2)
    r10 = xor_lsb        (LSB1 XOR LSB2)
    r11 = shift_save     (temp during bit counting)
"""

import sys

from bitstring import BitArray
from util import Machine


def main(vm: Machine | None = None) -> int:
    if vm is None:
        vm = Machine()

    # r2 <- min_dist (init to 16, the maximum possible Hamming distance)
    vm.ldi_I(BitArray(uint=16, length=8))
    vm.sto_R("r2")
    # r3 <- max_dist (init to 0)
    vm.ldi_I(BitArray(uint=0, length=8))
    vm.sto_R("r3")

    for i in range(32):
        for j in range(i + 1, 32):
            vm.ldi_I(BitArray(uint=i, length=8))
            vm.sto_R("r0")
            vm.ldi_I(BitArray(uint=j, length=8))
            vm.sto_R("r1")

            # r4 <- curr_dist = 0
            vm.ldi_I(BitArray(uint=0, length=8))
            vm.sto_R("r4")

            # r5 <- addr_msb1 = 2*i;  r6 <- addr_lsb1 = 2*i + 1
            vm.mov_R("r0")
            vm.shf_I(BitArray(int=1, length=8))
            vm.sto_R("r5")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r6")

            # r7 <- addr_msb2 = 2*j;  r8 <- addr_lsb2 = 2*j + 1
            vm.mov_R("r1")
            vm.shf_I(BitArray(int=1, length=8))
            vm.sto_R("r7")
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r8")

            # r9 <- MSB1 XOR MSB2
            vm.ld_R("r5")
            vm.sto_R("r9")
            vm.ld_R("r7")
            vm.xor_R("r9")
            vm.sto_R("r9")

            # r10 <- LSB1 XOR LSB2
            vm.ld_R("r6")
            vm.sto_R("r10")
            vm.ld_R("r8")
            vm.xor_R("r10")
            vm.sto_R("r10")

            # count set bits in r9 (MSB XOR), accumulate into r4
            vm.mov_R("r9")
            for _ in range(8):
                vm.shf_I(BitArray(int=1, length=8))
                if vm.carry_flag[0]:
                    vm.sto_R("r11")
                    vm.mov_R("r4")
                    vm.addi_I(BitArray(uint=1, length=8))
                    vm.sto_R("r4")
                    vm.mov_R("r11")

            # count set bits in r10 (LSB XOR), accumulate into r4
            vm.mov_R("r10")
            for _ in range(8):
                vm.shf_I(BitArray(int=1, length=8))
                if vm.carry_flag[0]:
                    vm.sto_R("r11")
                    vm.mov_R("r4")
                    vm.addi_I(BitArray(uint=1, length=8))
                    vm.sto_R("r4")
                    vm.mov_R("r11")

            # update min: if curr_dist < min_dist, min_dist = curr_dist
            vm.mov_R("r4")
            vm.cmp_R("r2")
            if vm.carry_flag[0]:
                vm.sto_R("r2")

            # update max: if max_dist < curr_dist, max_dist = curr_dist
            vm.mov_R("r3")
            vm.cmp_R("r4")
            if vm.carry_flag[0]:
                vm.mov_R("r4")
                vm.sto_R("r3")

    # store min_dist to mem[64], max_dist to mem[65]
    vm.ldi_I(BitArray(uint=64, length=8))
    vm.sto_R("r0")
    vm.mov_R("r2")
    vm.st_R("r0")

    vm.ldi_I(BitArray(uint=65, length=8))
    vm.sto_R("r0")
    vm.mov_R("r3")
    vm.st_R("r0")

    return 0


def test() -> None:
    import random as _random

    def _hamming(a: int, b: int) -> int:
        return bin((a ^ b) & 0xFFFF).count("1")

    def _run(values: list[int], label: str) -> None:
        vm = Machine()
        for idx, v in enumerate(values):
            vm.mem[idx * 2] = BitArray(uint=(v >> 8) & 0xFF, length=8)
            vm.mem[idx * 2 + 1] = BitArray(uint=v & 0xFF, length=8)
        main(vm)
        dists = [
            _hamming(values[i], values[j]) for i in range(32) for j in range(i + 1, 32)
        ]
        assert vm.mem[64].uint == min(dists), (
            f"{label}: min wrong (got {vm.mem[64].uint}, expected {min(dists)})"
        )
        assert vm.mem[65].uint == max(dists), (
            f"{label}: max wrong (got {vm.mem[65].uint}, expected {max(dists)})"
        )

    _run([0x0000] * 32, "all zeros")
    _run([0xFFFF] * 32, "all max")
    _run([0x0000] * 31 + [0xFFFF], "one differs maximally")
    _run([0x0000, 0xFFFF] + [0xAAAA] * 30, "two extremes plus alternating")
    _random.seed(42)
    _run([_random.randint(0, 0xFFFF) for _ in range(32)], "random seed 42")
    print("All tests passed!")


if __name__ == "__main__":
    test()
    sys.exit(main())
