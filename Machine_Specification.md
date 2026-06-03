# Machine Specification

## Instruction Formats

| TYPE | FORMAT | CORRESPONDING INSTRUCTIONS |
| :--- | :--- | :--- |
| **R/I (0)** | 1 bits type, 4 bits opcode, 4 bits register/immediate | and, xor, inv, add, sub, mov, sto, ld, st, cmp, jmp, shf, ldi, addi |
| **B (1)** | 1 bits type, 2 bits opcode, 6 bits instructions address | beq, bne, blt, bltu |

---

## Operations

| NAME | TYPE | BIT BREAKDOWN | EXAMPLE | NOTES |
| :--- | :--- | :--- | :--- | :--- |
| **and** = bitwise and with accumulator | R/I | 1 bit type (0), 4 bits opcode (0000), 4 bits register | `and r2`<br>0 0000 0010<br>`# ACC &= R2` | Clears carry_flag and overflow_flag. zero_flag set if the result is zero. sign_flag is MSB of the result. |
| **xor** = bitwise exclusive or with accumulator | R/I | 1 bit type (0), 4 bits opcode (0001), 4 bits register | `xor r1`<br>0 0001 0001<br>`# ACC ^= R1` | Clears carry_flag and overflow_flag. zero_flag set if the result is zero. sign_flag is MSB of the result. |
| **inv** = bitwise invert accumulator | R/I | 1 bit type (0), 4 bits opcode (0010), 4 bits register (XXXX) | `inv`<br>0 0010 0000<br>`# ACC = ~ACC` | Reg field unused. Preserves flags. |
| **add** = add register to accumulator | R/I | 1 bit type (0), 4 bits opcode (0011), 4 bits register | `add r2`<br>0 0011 0010<br>`# ACC += R2` | carry_flag set if there is an unsigned overflow. overflow_flag set if there is a signed overflow (both operands same sign, result differs). zero_flag set if the result is zero. sign_flag is MSB of the result. |
| **sub** = subtract register from accumulator | R/I | 1 bit type (0), 4 bits opcode (0100), 4 bits register | `sub r2`<br>0 0100 0010<br>`# ACC -= R2` | carry_flag set if there is an unsigned borrow. overflow_flag set if operands have opposite signs and result sign differs from acc. zero_flag set if the result is zero. sign_flag is MSB of the result. |
| **mov** = move register into accumulator | R/I | 1 bit type (0), 4 bits opcode (0101), 4 bits register | `mov r3`<br>0 0101 0011<br>`# ACC = R3` | Preserves flags. |
| **sto** = store accumulator into register | R/I | 1 bit type (0), 4 bits opcode (0110), 4 bits register | `sto r4`<br>0 0110 0100<br>`# R4 = ACC` | Preserves flags. |
| **ld** = load from memory into accumulator | R/I | 1 bit type (0), 4 bits opcode (0111), 4 bits register | `ld r1`<br>0 0111 0001<br>`# ACC = mem[R1]` | Preserves flags. |
| **st** = store accumulator into memory | R/I | 1 bit type (0), 4 bits opcode (1000), 4 bits register | `st r1`<br>0 1000 0001<br>`# mem[R1] = ACC` | Preserves flags. |
| **cmp** = compare accumulator to register | R/I | 1 bit type (0), 4 bits opcode (1001), 4 bits register | `cmp r3`<br>0 1001 0011<br>`# ACC - R3` | Performs a subtraction and discards the result, but saves the flags as follows: carry_flag set if there is an unsigned borrow; overflow_flag set if operands have opposite signs and result sign differs from acc; zero_flag set if the result is zero; sign_flag is the MSB of the result. |
| **jmp** = jump to a relative address specified by a register | R/I | 1 bit type (0), 4 bits opcode (1010), 4 bits register | `jmp r3`<br>0 1010 0011<br>`# PC += R3` | Used to handle jumps to large addresses, like when a loop is very long. |
| **shf** = signed shift accumulator | R/I | 1 bit type (0), 4 bits opcode (1011), 4 bits immediate | `shf 3`<br>0 1011 0011<br>`# ACC <<= 3`<br><br>`shf -1`<br>0 1011 1111<br>`# ACC >>= 1` | Immediate is a 4-bit two's complement (-8 to +7). Positive values shift left, and negative values shift right. carry_flag is set to the last bit shifted out. overflow_flag set if the sign bit changes during the shift; it is cleared at the start of every shf instruction. zero_flag set if the result is zero. sign_flag is the MSB of the result. |
| **ldi** = load immediate into accumulator | R/I | 1 bit type (0), 4 bits opcode (1100), 4 bits immediate | `ldi 5`<br>0 1100 0101<br>`# ACC = 5` | Immediate range 0-15 unsigned. Preserves flags. |
| **addi** = add immediate to accumulator | R/I | 1 bit type (0), 4 bits opcode (1101), 4 bits immediate | `addi 4`<br>0 1101 0100<br>`# ACC += 4`<br><br>`addi -3`<br>0 1101 1101<br>`# ACC -= 3` | Immediate is a 4-bit two's complement (-8 to +7). Replaces both addi and subi. Sets flags the same way as add. |
| **beq** = branch on equal | B | 1 bit type (1), 2 bits opcode (00), 6 bits instruction address | `beq 12`<br>1 00 001100<br>`# if ZF: PC += 12` | Branches if the zero flag is set after cmp. Relative address to PC. |
| **bne** = branch on not equal | B | 1 bit type (1), 2 bits opcode (01), 6 bits instruction address | `bne -12`<br>1 01 110100<br>`# if not ZF: PC -= 12` | Branches if zero flag isn't set after cmp. Relative address to PC. |
| **blt** = branch on less than | B | 1 bit type (1), 2 bits opcode (10), 6 bits instruction address | `blt 12`<br>1 10 001100<br>`# if SF != OF: PC += 12` | Branches if the sign flag is different from the overflow flag after cmp. Relative address to PC. |
| **bltu** = branch on less than (unsigned) | B | 1 bit type (1), 2 bits opcode (11), 6 bits instruction address | `bltu 12`<br>1 11 001100<br>`# if C: PC += 20` | Branches if the carry flag is set after cmp. Relative address to PC. |
