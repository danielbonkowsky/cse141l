"""
Write a program to find the least and greatest Hamming distances among all
pairs of values in an array of 32 two-byte half-words. Assume all values are
signed 16-bit (“half-word”) integers. The array of integers runs from data
memory location 0 to 63. Even-numbered addresses are MSBs, following odd
addresses are LSBs, e.g. a concatenation of addresses 0 and 1 forms a 16-bit
two's complement half-word. Write the minimum distance in location 64 and the
maximum in 65.
"""

import sys

from bitstring import BitArray
from util import Machine


def main(vm: Machine | None = None) -> int:
    if vm is None:
        vm = Machine()

    # initialize r0 <- min dist; r1 <- max dist
    vm.ldi_I(BitArray(bin="01111111"))
    vm.sto_R("r0")
    vm.ldi_I(BitArray(bin="00000000"))
    vm.sto_R("r1")

    for i in range(32):
        for j in range(i + 1, 32):
            # r2 <- i; r3 <- j ( not necessary for sim, but need to alloc in real asm code )
            vm.ldi_I(BitArray(uint=i, length=8))
            vm.sto_R("r2")
            vm.ldi_I(BitArray(uint=j, length=8))
            vm.sto_R("r3")

            # r4 <- curr dist
            vm.ldi_I(BitArray(bin="00000000"))
            vm.sto_R("r4")

            # r5 <- MSB1 addr
            vm.mov_R("r2")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.sto_R("r5")

            # r5 <- MSB1
            vm.ld_R("r5")
            vm.sto_R("r5")

            # r6 <- MSB2 addr
            vm.mov_R("r3")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.sto_R("r6")

            # acc <- MSB2
            vm.ld_R("r6")

            # MSB2 xor MSB1
            vm.xor_R("r5")

            # count how many ones
            for _ in range(8):
                # r5 will be loop counter in real asm
                vm.lsh_I(BitArray(uint=1, length=8))
                if vm.overflow_flag[0]:
                    # save acc in r6
                    vm.sto_R("r6")

                    # acc <- curr dist
                    vm.mov_R("r4")
                    vm.addi_I(BitArray(uint=1, length=8))

                    # r4 <- curr dist
                    vm.sto_R("r4")

                    # get acc back
                    vm.mov_R("r6")

            # r5 <- LSB1 addr
            vm.mov_R("r2")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r5")

            # r5 <- LSB1
            vm.ld_R("r5")
            vm.sto_R("r5")

            # r6 <- LSB2 addr
            vm.mov_R("r3")
            vm.lsh_I(BitArray(uint=1, length=8))
            vm.addi_I(BitArray(uint=1, length=8))
            vm.sto_R("r6")

            # acc <- LSB2
            vm.ld_R("r6")

            # LSB2 xor LSB1
            vm.xor_R("r5")

            # count how many ones
            for _ in range(8):
                # r5 will be loop counter in real asm
                vm.lsh_I(BitArray(uint=1, length=8))
                if vm.overflow_flag[0]:
                    # save acc in r6
                    vm.sto_R("r6")

                    # acc <- curr dist
                    vm.mov_R("r4")
                    vm.addi_I(BitArray(uint=1, length=8))

                    # r4 <- curr dist
                    vm.sto_R("r4")

                    # get acc back
                    vm.mov_R("r6")

            # Compare curr dist to min dist
            vm.mov_R("r4")
            vm.cmp_R("r0")
            if vm.sign_flag[0]:
                vm.sto_R("r0")

            # Compare curr dist to max dist
            vm.mov_R("r1")
            vm.cmp_R("r4")
            if vm.sign_flag[0]:
                vm.mov_R("r4")
                vm.sto_R("r1")

    # Store min dist into memory
    vm.ldi_I(BitArray(uint=64, length=8))
    vm.sto_R("r2")
    vm.mov_R("r0")
    vm.st_R("r2")

    # Store max dist into memory
    vm.ldi_I(BitArray(uint=65, length=8))
    vm.sto_R("r2")
    vm.mov_R("r1")
    vm.st_R("r2")

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
        dists = [_hamming(values[i], values[j]) for i in range(32) for j in range(i + 1, 32)]
        assert vm.mem[64].uint == min(dists), f"{label}: min wrong (got {vm.mem[64].uint}, expected {min(dists)})"
        assert vm.mem[65].uint == max(dists), f"{label}: max wrong (got {vm.mem[65].uint}, expected {max(dists)})"

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
