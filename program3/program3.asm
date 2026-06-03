# Program 3: signed 16x16 -> 32-bit shift-and-add multiply
# Translation of python_implementations/double_prec_mult.py.
#
# Input  mem[4N+0..3] = A_hi(signed), A_lo, B_hi(signed), B_lo   (N = 0..15)
# Output mem[64+4N+0..3] = product, MSB byte first
#
# Algorithm: sign-magnitude shift-and-add.
#   1. result_sign = sign(A) XOR sign(B)
#   2. convert A,B to unsigned magnitudes
#   3. for each of 16 multiplier bits (LSB first): if bit set, product +=
#      shifted_A; then shifted_A <<= 1
#   4. if result_sign, two's-complement-negate the 32-bit product
#
# Registers:
#   r0 = 0 (hardwired)        r1 = outer index N
#   r2 = carry/scratch        r3 = shifted_A byte0 (LSB) / |A_lo|
#   r4 = B_hi (>>'d)          r5 = B_lo (>>'d)   ({r4:r5} = 16-bit multiplier)
#   r6 = inner counter / address scratch         r7 = result_sign (0/1)
#   r8..r11  = product byte3(MSB)..byte0(LSB)
#   r12,r13,r14 = shifted_A byte3(MSB),byte2,byte1
#
# Carry idiom: the ISA has no add-with-carry / rotate-through-carry, so multi
# byte add/shift hold the running carry in r2 (0/1), materialized from the
# carry_flag via local bltu branches. Per byte the two possible carries are
# mutually exclusive (see double_prec_mult.py), so carry-out is a single bit.
# 'and r0; beq L' is a 2-instruction unconditional jump (ACC->0 sets Z).

    ldi 0; sto r1                  # N = 0

OUTER:
    # ── load operands A_hi,A_lo,B_hi,B_lo from mem[4N..4N+3] ──
    mov r1; shf 2; sto r6          # r6 = 4N
    ld r6; sto r2                  # r2 = A_hi
    mov r6; addi 1; sto r6; ld r6; sto r3   # r3 = A_lo
    mov r6; addi 1; sto r6; ld r6; sto r4   # r4 = B_hi
    mov r6; addi 1; sto r6; ld r6; sto r5   # r5 = B_lo

    # ── result_sign = sign(A) XOR sign(B)  (bit7 of each MSB) ──
    mov r2; shf -7; sto r7
    mov r4; shf -7; xor r7; sto r7 # r7 = a_neg ^ b_neg

    # ── magnitude of A: if a_neg, negate {r2:r3} ──
    mov r2; shf -7; cmp r0         # a_neg ? (Z if not)
    beq SKIP_NEGA
    mov r3; inv; addi 1; sto r3    # A_lo = ~A_lo + 1
    bltu NEGA_HC
    mov r2; inv; sto r2
    and r0; beq SKIP_NEGA
NEGA_HC:
    mov r2; inv; addi 1; sto r2
SKIP_NEGA:

    # ── magnitude of B: if b_neg, negate {r4:r5} ──
    mov r4; shf -7; cmp r0
    beq SKIP_NEGB
    mov r5; inv; addi 1; sto r5
    bltu NEGB_HC
    mov r4; inv; sto r4
    and r0; beq SKIP_NEGB
NEGB_HC:
    mov r4; inv; addi 1; sto r4
SKIP_NEGB:

    # ── product = 0 ; shifted_A = {0,0,|A_hi|,|A_lo|} ──
    ldi 0; sto r8; sto r9; sto r10; sto r11
    ldi 0; sto r12; sto r13
    mov r2; sto r14                # shifted_A byte1 = |A_hi|  (r3 already = |A_lo|)
    ldi 0; sto r6                  # inner counter = 0

INNER:
    # multiplier bit = bit0 of r5 ; then r5 >>= 1
    mov r5; shf -1; sto r5         # carry = multiplier bit
    bltu DOADD
    jmpl SHIFTP r2                 # bit = 0: skip the add

DOADD:
    # ── product += shifted_A  (32-bit add, carry in r2) ──
    # byte0 (LSB): r11 += r3
    mov r11; add r3; sto r11
    bltu A0C1
    ldi 0; sto r2
    and r0; beq A0D
A0C1:
    ldi 1; sto r2
A0D:
    # byte1: r10 += r14 + carry
    mov r10; add r14; sto r10
    bltu A1CA
    mov r10; add r2; sto r10
    bltu A1CB
    ldi 0; sto r2
    and r0; beq A1D
A1CB:
    ldi 1; sto r2
    and r0; beq A1D
A1CA:
    mov r10; add r2; sto r10
    ldi 1; sto r2
A1D:
    # byte2: r9 += r13 + carry
    mov r9; add r13; sto r9
    bltu A2CA
    mov r9; add r2; sto r9
    bltu A2CB
    ldi 0; sto r2
    and r0; beq A2D
A2CB:
    ldi 1; sto r2
    and r0; beq A2D
A2CA:
    mov r9; add r2; sto r9
    ldi 1; sto r2
A2D:
    # byte3 (MSB): r8 += r12 + carry  (carry-out discarded)
    mov r8; add r12; sto r8
    mov r8; add r2; sto r8

SHIFTP:
    # ── shifted_A <<= 1  (32-bit left shift, carry in r2) ──
    # byte0 (LSB) r3, carry-in = 0
    mov r3; shf 1; sto r3
    bltu S0C1
    ldi 0; sto r2
    and r0; beq S0D
S0C1:
    ldi 1; sto r2
S0D:
    # byte1 r14
    mov r14; shf 1; sto r14
    bltu S1C1
    mov r14; add r2; sto r14
    ldi 0; sto r2
    and r0; beq S1D
S1C1:
    mov r14; add r2; sto r14
    ldi 1; sto r2
S1D:
    # byte2 r13
    mov r13; shf 1; sto r13
    bltu S2C1
    mov r13; add r2; sto r13
    ldi 0; sto r2
    and r0; beq S2D
S2C1:
    mov r13; add r2; sto r13
    ldi 1; sto r2
S2D:
    # byte3 (MSB) r12  (carry-out discarded)
    mov r12; shf 1; sto r12
    mov r12; add r2; sto r12

    # ── finish 16-bit B >> : inject old r4.bit0 into r5.bit7, then r4 >>= 1 ──
    mov r4; shf -1; sto r4         # carry = bit to inject
    bltu INJ
    and r0; beq NOINJ
INJ:
    ldi 8; shf 4; add r5; sto r5   # r5 |= 0x80
NOINJ:

    # ── inner loop control (16 iterations) ──
    mov r6; addi 1; sto r6
    ldi 8; shf 1; sto r2           # r2 = 16
    mov r6; cmp r2
    beq INNER_DONE
    jmpl INNER r2
INNER_DONE:

    # ── apply sign: if r7, two's-complement-negate the 32-bit product ──
    mov r0; cmp r7                 # Z if r7 == 0
    beq AFTER_NEG32                # positive: skip (short forward branch)
    # invert all four bytes
    mov r11; inv; addi 1; sto r11  # ~r11 + 1 ; carry
    mov r10; inv; sto r10          # ~r10  (carry preserved)
    bltu NG1
    and r0; beq NG1D
NG1:
    addi 1; sto r10
NG1D:
    mov r9; inv; sto r9
    bltu NG2
    and r0; beq NG2D
NG2:
    addi 1; sto r9
NG2D:
    mov r8; inv; sto r8
    bltu NG3
    and r0; beq NG3D
NG3:
    addi 1; sto r8
NG3D:
AFTER_NEG32:

    # ── store product to mem[64+4N .. +3], MSB first ──
    mov r1; shf 2; sto r6          # 4N
    ldi 8; shf 3; add r6; sto r6   # 64 + 4N
    mov r8; st r6
    mov r6; addi 1; sto r6; mov r9;  st r6
    mov r6; addi 1; sto r6; mov r10; st r6
    mov r6; addi 1; sto r6; mov r11; st r6

    # ── outer loop control ──
    mov r1; addi 1; sto r1         # N++
    ldi 8; shf 1; sto r6           # r6 = 16
    mov r1; cmp r6
    beq PROG_DONE
    jmpl OUTER r6
PROG_DONE:
    done
