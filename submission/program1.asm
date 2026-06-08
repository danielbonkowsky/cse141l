# Program 1: Closest and Farthest Hamming Pairs
# Input:  mem[0..63]  (32 16-bit values; MSB at even addr, LSB at odd addr)
# Output: mem[64] = min Hamming distance, mem[65] = max Hamming distance
#
# Registers (16 available — no memory spills):
#   r0=0  r1=min  r2=max  r3=i  r4=j  r5=XOR/scratch
#   r6=popcount acc  r7=const 1  r8=addr temp / jmp target
#   r9=MSB popcount  r10=total dist
#
# ISA: shf +k=left, -k=right;  cmp carry=1 on unsigned borrow (ACC<reg)
#      bltu=branch on carry;  bne=branch on zero clear;  JMP absolute
#      Program loaded at address 0; jmpl LABEL rN loads addr into rN, jmp rN

# ─── INIT ───────────────────────────────────────────────────────────────────
    ldi 1
    sto r7              # r7 = 1 (bitmask)
    ldi 15
    addi 1
    sto r1              # r1 = 16 (min)
    ldi 0
    sto r2              # r2 = 0  (max)
    ldi 0
    sto r3              # r3 = 0  (i)

OUTER_LOOP:
    mov r3
    addi 1
    sto r4              # j = i + 1

INNER_LOOP:
    # MSB_j = mem[2j]
    mov r4; shf 1; sto r8; ld r8; sto r5        # r5 = MSB_j
    # MSB_i = mem[2i], XOR
    mov r3; shf 1; sto r8; ld r8; xor r5; sto r5  # r5 = MSB XOR

    # popcount(r5) → r6
    ldi 0; sto r6
    mov r5; and r7; add r6; sto r6              # bit 0
    mov r5; shf -1; and r7; add r6; sto r6      # bit 1
    mov r5; shf -2; and r7; add r6; sto r6      # bit 2
    mov r5; shf -3; and r7; add r6; sto r6      # bit 3
    mov r5; shf -4; and r7; add r6; sto r6      # bit 4
    mov r5; shf -5; and r7; add r6; sto r6      # bit 5
    mov r5; shf -6; and r7; add r6; sto r6      # bit 6
    mov r5; shf -7; and r7; add r6; sto r6      # bit 7
    mov r6; sto r9                              # r9 = popcount(MSB XOR)

    # LSB_j = mem[2j+1]
    mov r4; shf 1; addi 1; sto r8; ld r8; sto r5   # r5 = LSB_j
    # LSB_i = mem[2i+1], XOR
    mov r3; shf 1; addi 1; sto r8; ld r8; xor r5; sto r5  # r5 = LSB XOR

    # popcount(r5) → r6
    ldi 0; sto r6
    mov r5; and r7; add r6; sto r6              # bit 0
    mov r5; shf -1; and r7; add r6; sto r6      # bit 1
    mov r5; shf -2; and r7; add r6; sto r6      # bit 2
    mov r5; shf -3; and r7; add r6; sto r6      # bit 3
    mov r5; shf -4; and r7; add r6; sto r6      # bit 4
    mov r5; shf -5; and r7; add r6; sto r6      # bit 5
    mov r5; shf -6; and r7; add r6; sto r6      # bit 6
    mov r5; shf -7; and r7; add r6; sto r6      # bit 7

    # total dist = MSB + LSB popcount
    mov r9; add r6; sto r10                     # r10 = dist

    # ── MIN CHECK ──
    mov r10; cmp r1                             # dist - min; carry=1 if dist<min
    bltu TRAMP_MIN                              # dist < min → update

    # ── MAX CHECK ──
MAX_CHECK:
    mov r2; cmp r10                             # max - dist; carry=1 if dist>max
    bltu TRAMP_MAX                              # dist > max → update

    # ── J LOOP CONTROL ──
LOOP_CTL:
    mov r4; addi 1; sto r4                      # j++
    ldi 8; shf 2; sto r8                        # r8 = 32
    mov r4; cmp r8                              # j - 32
    bne INNER_BACK                             # j != 32: loop back

    # ── I LOOP CONTROL ──
    # Stop when i == 31: pair (i,31) for all i<31 is already covered, and
    # i=31 would start j at 32 (out of range). r8 currently = 32 → make it 31.
    mov r3; addi 1; sto r3                      # i++
    mov r8; addi -1; sto r8                     # r8 = 31
    mov r3; cmp r8                              # i - 31
    bne OUTER_BACK                             # i != 31: outer loop
    beq STORE                                  # i == 31: jump over trampolines

# ─── TRAMPOLINES + BACK-JUMPS (kept near the branches; jmp away) ────────────
TRAMP_MIN:
    jmpl DO_MIN r8
TRAMP_MAX:
    jmpl DO_MAX r8
INNER_BACK:
    jmpl INNER_LOOP r8
OUTER_BACK:
    jmpl OUTER_LOOP r8

STORE:
    ldi 8; shf 3; sto r8                        # r8 = 64
    mov r1; st r8                               # mem[64] = min
    mov r8; addi 1; sto r8                      # r8 = 65
    mov r2; st r8                               # mem[65] = max
    done

# ─── UPDATE BLOCKS (reached only via trampolines) ───────────────────────────
DO_MIN:
    mov r10; sto r1; jmpl MAX_CHECK r8          # min = dist, back to max check
DO_MAX:
    mov r10; sto r2; jmpl LOOP_CTL r8           # max = dist, back to loop control
