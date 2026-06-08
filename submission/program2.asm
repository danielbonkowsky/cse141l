# Program 2: Arithmetic Distance (min/max |num1 - num2|)
# Input:  mem[0..63] = 32 signed 16-bit values (MSB even, LSB odd)
# Output: mem[66:67] = min |diff| (MSB:LSB), mem[68:69] = max |diff| (MSB:LSB)
#
# Distance can be up to 65535 (e.g. 32767 - (-32768)), so it's a 16-bit
# UNSIGNED value. We can't compute num1-num2 directly (signed overflow), so:
#   1. signed-compare num1 vs num2 (compare MSBs signed; if equal, LSBs unsigned)
#   2. swap so (r9:r10) = greater, (r11:r12) = lesser
#   3. dist = greater - lesser  (16-bit unsigned subtract; result fits in 16 bits)
#   4. update min/max with 16-bit unsigned compares
#
# Registers:
#   r0=0  r1=min_msb  r2=min_lsb  r3=max_msb  r4=max_lsb
#   r5=i  r6=j  r7=const 1  r8=addr / jmp scratch
#   r9,r10  = num1 / greater (msb,lsb)
#   r11,r12 = num2 / lesser  (msb,lsb)
#   r13,r14 = dist (msb,lsb)   r15 = swap temp
#
# ISA: shf +k=left -k=right; cmp carry=1 on unsigned borrow (ACC<reg);
#      blt=signed <  (S!=V);  bltu=unsigned < (carry);  bne/beq=zero;
#      'and r0; beq L' = 2-instruction unconditional jump (ACC->0, Z=1)
#      JMP absolute; jmpl LABEL rN; program loaded at address 0

# ─── INIT ───────────────────────────────────────────────────────────────────
    ldi 1; sto r7                  # r7 = 1
    ldi 0; inv; sto r1; sto r2     # min = 0xFFFF (r1=r2=255)
    ldi 0; sto r3; sto r4; sto r5  # max = 0 (r3=r4=0), i = 0

OUTER_LOOP:
    mov r5; addi 1; sto r6         # j = i + 1

INNER_LOOP:
    # ── Load num1 = mem[2i]:mem[2i+1] → r9:r10 ──
    mov r5; shf 1; sto r8; ld r8; sto r9          # r9  = num1_msb
    mov r5; shf 1; addi 1; sto r8; ld r8; sto r10 # r10 = num1_lsb
    # ── Load num2 = mem[2j]:mem[2j+1] → r11:r12 ──
    mov r6; shf 1; sto r8; ld r8; sto r11         # r11 = num2_msb
    mov r6; shf 1; addi 1; sto r8; ld r8; sto r12 # r12 = num2_lsb

    # ── Signed compare num1 vs num2; swap so r9:r10 = greater ──
    mov r9; cmp r11                # signed MSB compare (num1_msb - num2_msb)
    blt DO_SWAP                    # num1 < num2 (signed msb) → swap
    bne AFTER_SWAP                 # num1 > num2 (msb differ) → no swap
    mov r10; cmp r12              # MSBs equal → unsigned LSB compare
    bltu DO_SWAP                   # num1_lsb < num2_lsb → num1 < num2 → swap
    bne AFTER_SWAP                 # num1_lsb > num2_lsb → no swap
    beq AFTER_SWAP                 # equal (num1 == num2) → no swap
DO_SWAP:
    mov r9;  sto r8; mov r11; sto r9;  mov r8; sto r11   # swap msbs
    mov r10; sto r8; mov r12; sto r10; mov r8; sto r12   # swap lsbs
AFTER_SWAP:
    # r9:r10 = greater, r11:r12 = lesser

    # ── dist = greater - lesser  (16-bit unsigned) → r13:r14 ──
    mov r10; sub r12; sto r14      # dist_lsb = greater_lsb - lesser_lsb; carry=borrow
    bltu MSB_BORROW                # borrow → subtract extra 1 from msb
    mov r9; sub r11; sto r13       # dist_msb (no borrow)
    and r0; beq HAVE_DIST          # uncond jump over borrow path
MSB_BORROW:
    mov r9; sub r11; sub r7; sto r13   # dist_msb - 1 (borrow)
HAVE_DIST:

    # ── MIN UPDATE: if dist < min, min = dist  (16-bit unsigned) ──
    mov r13; cmp r1                # dist_msb vs min_msb
    bltu DO_MIN                    # dist_msb < min_msb → update
    bne SKIP_MIN                   # dist_msb > min_msb → skip
    mov r14; cmp r2               # MSBs equal → compare LSBs
    bltu DO_MIN                    # dist_lsb < min_lsb → update
    bne SKIP_MIN                   # dist_lsb > min_lsb → skip
    beq SKIP_MIN                   # equal → skip
DO_MIN:
    mov r13; sto r1; mov r14; sto r2   # min = dist
SKIP_MIN:

    # ── MAX UPDATE: if dist > max, max = dist  (16-bit unsigned) ──
    mov r3; cmp r13                # max_msb vs dist_msb
    bltu DO_MAX                    # max_msb < dist_msb → max < dist → update
    bne SKIP_MAX                   # max_msb > dist_msb → skip
    mov r4; cmp r14               # MSBs equal → compare LSBs
    bltu DO_MAX                    # max_lsb < dist_lsb → update
    bne SKIP_MAX                   # max_lsb > dist_lsb → skip
    beq SKIP_MAX                   # equal → skip
DO_MAX:
    mov r13; sto r3; mov r14; sto r4   # max = dist
SKIP_MAX:

    # ── J LOOP CONTROL ──
    mov r6; addi 1; sto r6         # j++
    ldi 8; shf 2; sto r8           # r8 = 32
    mov r6; cmp r8                 # j - 32
    bne INNER_BACK                 # j != 32: loop back

    # ── I LOOP CONTROL ──  (stop at i==31; pair (i,31) already covered)
    mov r5; addi 1; sto r5         # i++
    mov r8; addi -1; sto r8        # r8 = 31
    mov r5; cmp r8                 # i - 31
    bne OUTER_BACK                 # i != 31: outer loop
    beq STORE                      # i == 31: done

# ─── TRAMPOLINES (kept near branches; jmp away) ─────────────────────────────
INNER_BACK:
    jmpl INNER_LOOP r8
OUTER_BACK:
    jmpl OUTER_LOOP r8

# ─── STORE RESULTS ──────────────────────────────────────────────────────────
STORE:
    ldi 8; shf 3; addi 2; sto r8   # r8 = 66
    mov r1; st r8                  # mem[66] = min_msb
    mov r8; addi 1; sto r8         # 67
    mov r2; st r8                  # mem[67] = min_lsb
    mov r8; addi 1; sto r8         # 68
    mov r3; st r8                  # mem[68] = max_msb
    mov r8; addi 1; sto r8         # 69
    mov r4; st r8                  # mem[69] = max_lsb
    done
