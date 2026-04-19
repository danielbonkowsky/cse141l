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


def main() -> int:
    vm = Machine()

    # r1 will hold the msb of the min
    vm.set_reg("r1", BitArray(uint=255, length=8))        # mov r1, #255

    # r2 will hold the lsb of the min
    vm.set_reg("r2", BitArray(uint=255, length=8))        # mov r2, #255

    # r3 will hold the msb of the max
    vm.set_reg("r3", BitArray(uint=0, length=8))          # mov r3, #0

    # r4 will hold the lsb of the max
    vm.set_reg("r4", BitArray(uint=0, length=8))          # mov r4, #0

    for i in range(32):
        for j in range(i + 1, 32):
            # r5 will hold the msb of num1
            vm.get_mem("r5", 2 * i)                       # mov r5, [2 * i]

            # r6 will hold the lsb of num1
            vm.get_mem("r6", 2 * i + 1)                   # mov r6, [2 * i + 1]

            # r7 will hold the msb of num2
            vm.get_mem("r7", 2 * j)                       # mov r7, [2 * j]

            # r8 will hold the lsb of num2
            vm.get_mem("r8", 2 * j + 1)                   # mov r8, [2 * j + 1]

            # signed-compare the msbs
            vm.scmp("r5", "r7")                           # scmp r5, r7

            # are they equal?
            if vm.zero_flag.uint == 1:
                # unsigned-compare the lsbs
                vm.ucmp("r6", "r8")                       # ucmp r6, r8

                # is num1 < num2?
                if vm.sign_flag.uint == 1:
                    # r9 will hold the lesser msb
                    vm.set_reg("r9", vm.get_reg("r5"))    # mov r9, r5

                    # r10 will hold the lesser lsb
                    vm.set_reg("r10", vm.get_reg("r6"))   # mov r10, r6

                    # r11 will hold the greater msb
                    vm.set_reg("r11", vm.get_reg("r7"))   # mov r11, r7

                    # r12 will hold the greater lsb
                    vm.set_reg("r12", vm.get_reg("r8"))   # mov r12, r8
                else:
                    # r9 will hold the lesser msb
                    vm.set_reg("r9", vm.get_reg("r7"))    # mov r9, r7

                    # r10 will hold the lesser lsb
                    vm.set_reg("r10", vm.get_reg("r8"))   # mov r10, r8

                    # r11 will hold the greater msb
                    vm.set_reg("r11", vm.get_reg("r5"))   # mov r11, r5

                    # r12 will hold the greater lsb
                    vm.set_reg("r12", vm.get_reg("r6"))   # mov r12, r6
            
            # is num1 < num2?
            elif vm.sign_flag.uint == 1:
                # r9 will hold the lesser msb
                vm.set_reg("r9", vm.get_reg("r5"))        # mov r9, r5

                # r10 will hold the lesser lsb
                vm.set_reg("r10", vm.get_reg("r6"))       # mov r10, r6

                # r11 will hold the greater msb
                vm.set_reg("r11", vm.get_reg("r7"))       # mov r11, r7

                # r12 will hold the greater lsb
                vm.set_reg("r12", vm.get_reg("r8"))       # mov r12, r8
            else:
                # r9 will hold the lesser msb
                vm.set_reg("r9", vm.get_reg("r7"))        # mov r9, r7

                # r10 will hold the lesser lsb
                vm.set_reg("r10", vm.get_reg("r8"))       # mov r10, r8

                # r11 will hold the greater msb
                vm.set_reg("r11", vm.get_reg("r5"))       # mov r11, r5

                # r12 will hold the greater lsb
                vm.set_reg("r12", vm.get_reg("r6"))       # mov r12, r6
            
            # negate the lesser num
            vm.invert_reg("r9")                           # inv r9
            vm.invert_reg("r10")                          # inv r10
            vm.set_reg("r16", BitArray(uint=1, length=8)) # mov r16, #1
            vm.add("r10", "r10", "r16")                   # add r10, r10, r16
            if vm.carry_flag.uint == 1:
                vm.add("r9", "r9", "r16")                 # add r9, r9, r16
            
            # r5 will hold the dist msb
            vm.add("r5", "r11", "r9")                     # add r5, r11, r9

            # r6 will hold the dist lsb
            vm.add("r6", "r12", "r10")                    # add r6, r12, r10

            # propogate carry
            if vm.carry_flag.uint == 1:
                vm.add("r5", "r5", "r16")                # add r5, r5, r16
            
            # unsigned-compare dist msb and min msb
            vm.ucmp("r5", "r1")                           # ucmp r5, r1
            
            # are they equal?
            if vm.zero_flag.uint == 1:
                # compare lsbs
                vm.ucmp("r6", "r2")

                # dist < min?
                if vm.sign_flag.uint == 1:
                    # set min = dist
                    vm.set_reg("r1", vm.get_reg("r5"))    # mov r1, r5
                    vm.set_reg("r2", vm.get_reg("r6"))    # mov r2, r6

            # is dist < min?
            elif vm.sign_flag.uint == 1:
                # set min = dist
                vm.set_reg("r1", vm.get_reg("r5"))        # mov r1, r5
                vm.set_reg("r2", vm.get_reg("r6"))        # mov r2, r6
            
            # unsigned-compare max msb and dist msb
            vm.ucmp("r3", "r5")                           # ucmp r3, r5

            # are they equal?
            if vm.zero_flag.uint == 1:
                # compare lsbs
                vm.ucmp("r4", "r6")                       # ucmp r4, r6

                # is max < dist?
                if vm.sign_flag.uint == 1:
                    # set max = dist
                    vm.set_reg("r3", vm.get_reg("r5"))    # mov r3, r5
                    vm.set_reg("r4", vm.get_reg("r6"))    # mov r4, r6
                
            # is max < dist?
            elif vm.sign_flag.uint == 1:
                # set max = dist
                vm.set_reg("r3", vm.get_reg("r5"))        # mov r3, r5
                vm.set_reg("r4", vm.get_reg("r6"))        # mov r4, r6
    
    # write min to memory
    vm.set_mem(66, "r1")                                  # mov [#66], r1
    vm.set_mem(67, "r2")                                  # mov [#67], r2

    # write max to memory
    vm.set_mem(68, "r3")                                  # mov [#68], r3
    vm.set_mem(69, "r4")                                  # mov [#69], r4

    print(f"The minimum arithmetic distance was {256 * vm.mem[66].uint + vm.mem[67].uint}")
    print(f"The maximum arithmetic distance was {256 * vm.mem[68].uint + vm.mem[69].uint}")


if __name__ == "__main__":
    sys.exit(main())
