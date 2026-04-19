"""
Write a program to find the least and greatest Hamming distances among all 
pairs of values in an array of 32 two-byte half-words. Assume all values are 
signed 16-bit (“half-word”) integers. The array of integers runs from data 
memory location 0 to 63. Even-numbered addresses are MSBs, following odd 
addresses are LSBs, e.g. a concatenation of addresses 0 and 1 forms a 16-bit 
two's complement half-word. Write the minimum distance in location 64 and the 
maximum in 65.
"""


from bitstring import BitArray
import sys
from util import Machine


def main() -> int:
    vm = Machine()

    # r1 will hold min Hamming dist
    vm.set_reg("r1", BitArray(uint=16, length=8))  # mov r1, #16

    # r2 will hold max Hamming dist
    vm.set_reg("r2", BitArray(uint=0, length=8))   # mov r2, #0

    for i in range(32):
        for j in range(i + 1, 32):
            # r3 will hold msb1
            vm.get_mem("r3", i * 2)                # mov r3, [i * 2]

            # r4 will hold msb2
            vm.get_mem("r4", j * 2)                # mov r4, [j * 2]

            # r5 will hold r3 ^ r4
            vm.xor("r5", "r3", "r4")               # xor r5, r3, r4

            # r6 will hold the number of ones in r5
            vm.count_ones("r6", "r5")              # cto r6, r5

            # r3 will hold lsb1
            vm.get_mem("r3", i * 2 + 1)            # mov r3, [i * 2 + 1]

            # r4 will hold lsb2
            vm.get_mem("r4", j * 2 + 1)            # mov r4, [j * 2 + 1]

            # r5 will hold r3 ^ r4
            vm.xor("r5", "r3", "r4")               # xor r5, r3, r4

            # r7 will hold the number of ones in r5
            vm.count_ones("r7", "r5")              # cto r7, r5

            # r7 will hold r6 + r7 (Hamming dist for this pair)
            vm.add("r7", "r6", "r7")               # add r7, r6, r7

            # compare r7 to the current min
            vm.ucmp("r7", "r1")                    # ucmp r7, r1

            # check if it's smaller than current min
            if vm.sign_flag.uint == 1:
                vm.set_reg("r1", vm.get_reg("r7")) # mov r1, r7
            
            # compare r7 to the current max
            vm.ucmp("r2", "r7")                    # ucmp r2, r7

            # check if the current max is smaller than r7
            if vm.sign_flag.uint == 1:
                vm.set_reg("r2", vm.get_reg("r7")) # mov r2, r7
    
    # write min dist to memory
    vm.set_mem(64, "r1")                           # mov [#64], r1

    # write max dist to memory
    vm.set_mem(65, "r2")                           # mov [#65], r2

    print(f"The minimum Hamming distance was {vm.mem[64].uint}")
    print(f"The maximum Hamming distance was {vm.mem[65].uint}")

    return 0


if __name__ == "__main__": 
    sys.exit(main())
