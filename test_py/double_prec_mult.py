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

def main() -> int:
    vm = Machine()

    vm.set_reg("r16", BitArray(uint=0, length=8))
    vm.set_reg("r15", BitArray(uint=1, length=8))

    for n in range(16):
        # r1 will hold most significant (signed) byte of operand A_N
        vm.get_mem("r1", 4 * n)      # mov r1, [4 * n]

        # r2 will hold least significant (unsigned) byte of operand A_N
        vm.get_mem("r2", 4 * n + 1)  # mov r2, [4 * n + 1]

        # if A_N is negative, make it positive
        vm.lsh("r1", 1)
        vm.get_mem("r1", 4 * n)     # mov r1, [4 * n]
        if vm.overflow_flag.uint == 1:
            vm.invert_reg("r1")
            vm.invert_reg("r2")
            vm.add("r2", "r2", "r15")
            if vm.overflow_flag.uint == 1:
                vm.add("r1", "r1", "r15")
        
        # r3 will hold most significant (signed) byte of operand B_N
        vm.get_mem("r3", 4 * n + 2)  # mov r3, [4 * n + 2]

        # r4 will hold least significant (unsigned) byte of operand B_N
        vm.get_mem("r4", 4 * n + 3)  # mov r4, [4 * n + 3]

        # if B_N is negative, make it positive
        vm.lsh("r3", 1)
        vm.get_mem("r3", 4 * n + 2)  # mov r3, [4 * n + 2]
        if vm.overflow_flag.uint == 1:
            vm.invert_reg("r3")
            vm.invert_reg("r4")
            vm.add("r4", "r4", "r15")
            if vm.overflow_flag.uint == 1:
                vm.add("r3", "r3", "r15")

        # Zero out result
        vm.set_mem(64 + 4 * n + 0, "r16")
        vm.set_mem(64 + 4 * n + 1, "r16")
        vm.set_mem(64 + 4 * n + 2, "r16")
        vm.set_mem(64 + 4 * n + 3, "r16")

        vm.set_reg("r14", BitArray(uint=1, length=8))
        for i in range(8):
            # Check if the current bit is 1
            vm.and_reg("r13", "r4", "r14")
            vm.ucmp("r13", "r16")
            if vm.zero_flag.uint == 1:
                # If it is, skip adding and shift mask bit
                vm.lsh("r14", 1)                
                continue

            # r5 will hold shifted r4
            vm.set_reg("r5", vm.get_reg("r4"))
            vm.lsh("r5", i)

            # Add to LSB
            vm.get_mem("r6", 64 + 4 * n + 3)
            vm.add("r6", "r6", "r5")
            vm.set_mem(64 + 4 * n + 3, "r6")

            # Propogate carry
            if vm.overflow_flag.uint == 1:
                vm.get_mem("r6", 64 + 4 * n + 2)
                vm.add("r6", "r6", "r15")
                vm.set_mem(64 + 4 * n + 2, "r6")
                if vm.overflow_flag.uint == 1:
                    vm.get_mem("r6", 64 + 4 * n + 1)
                    vm.add("r6", "r6", "r15")
                    vm.set_mem(64 + 4 * n + 1, "r6")
                    if vm.overflow_flag.uint == 1:
                        vm.get_mem("r6", 64 + 4 * n + 0)
                        vm.add("r6", "r6", "r15")
                        vm.set_mem(64 + 4 * n + 0, "r6")
            
            # r5 will hold shifted r4
            vm.set_reg("r5", vm.get_reg("r4"))
            vm.rsh("r5", 8 - i)

            # Add to 3rd byte
            vm.get_mem("r6", 64 + 4 * n + 2)
            vm.add("r6", "r6", "r5")
            vm.set_mem(64 + 4 * n + 2, "r6")

            # Propogate carry
            if vm.overflow_flag.uint == 1:
                vm.get_mem("r6", 64 + 4 * n + 1)
                vm.add("r6", "r6", "r15")
                vm.set_mem(64 + 4 * n + 1, "r6")
                if vm.overflow_flag.uint == 1:
                    vm.get_mem("r6", 64 + 4 * n + 0)
                    vm.add("r6", "r6", "r15")
                    vm.set_mem(64 + 4 * n + 0, "r6")     

            # Left shift mask
            vm.lsh("r14", 1)

        vm.set_reg("r14", BitArray(uint=1, length=8))
        for i in range(8):
            # Check if the current bit is 1
            vm.and_reg("r13", "r3", "r14")
            vm.ucmp("r13", "r16")
            if vm.zero_flag.uint == 1:
                # If it is, shift mask bit and skip
                vm.lsh("r14", 1)                
                continue

            # r5 will hold shifted r3
            vm.set_reg("r5", vm.get_reg("r3"))
            vm.lsh("r5", i)

            # Add to 2nd byte
            vm.get_mem("r6", 64 + 4 * n + 1)
            vm.add("r6", "r6", "r5")
            vm.set_mem(64 + 4 * n + 1, "r6")

            # Propogate carry
            if vm.overflow_flag.uint == 1:
                vm.get_mem("r6", 64 + 4 * n + 0)
                vm.add("r6", "r6", "r15")
                vm.set_mem(64 + 4 * n + 0, "r6")
            
            # r5 will hold shifted r3
            vm.set_reg("r5", vm.get_reg("r3"))
            vm.rsh("r5", 8 - i)

            # Add to MSB
            vm.get_mem("r6", 64 + 4 * n + 0)
            vm.add("r6", "r6", "r5")
            vm.set_mem(64 + 4 * n + 0, "r6") 

            # Left shift mask
            vm.lsh("r14", 1)
        
        # r1 will hold the most significant (signed) byte of operand A_N
        vm.get_mem("r1", 4 * n)

        # r2 will hold most significant (signed) byte of operand B_N
        vm.get_mem("r2", 4 * n + 2)  # mov r2, [4 * n + 2]

        # r3 will hold the xor of r1, r2
        vm.xor("r3", "r1", "r2")

        # save only the leftmost bit
        vm.set_reg("r14", BitArray(bin="10000000"))
        vm.and_reg("r3", "r3", "r14")

        # check if it's zero
        vm.ucmp("r3", "r16")
        if vm.zero_flag.uint != 1:
            # negate the result
            vm.get_mem("r1", 64 + 4 * n + 0)
            vm.invert_reg("r1")
            vm.set_mem(64 + 4 * n + 0, "r1")

            vm.get_mem("r1", 64 + 4 * n + 1)
            vm.invert_reg("r1")
            vm.set_mem(64 + 4 * n + 1, "r1")

            vm.get_mem("r1", 64 + 4 * n + 2)
            vm.invert_reg("r1")
            vm.set_mem(64 + 4 * n + 2, "r1")

            vm.get_mem("r1", 64 + 4 * n + 3)
            vm.invert_reg("r1")
            vm.set_mem(64 + 4 * n + 3, "r1")

            # add 1
            vm.get_mem("r1", 64 + 4 * n + 0)
            vm.add("r1", "r1", "r15")
            vm.set_mem(64 + 4 * n + 0, "r1")
            if vm.overflow_flag.uint == 1:
                vm.get_mem("r1", 64 + 4 * n + 1)
                vm.add("r1", "r1", "r15")
                vm.set_mem(64 + 4 * n + 1, "r1")
                if vm.overflow_flag.uint == 1:
                    vm.get_mem("r1", 64 + 4 * n + 2)
                    vm.add("r1", "r1", "r15")
                    vm.set_mem(64 + 4 * n + 2, "r1")
                    if vm.overflow_flag.uint == 1:
                        vm.get_mem("r1", 64 + 4 * n + 3)
                        vm.add("r1", "r1", "r15")
                        vm.set_mem(64 + 4 * n + 3, "r1")


if __name__ == "__main__":
    sys.exit(main())
        