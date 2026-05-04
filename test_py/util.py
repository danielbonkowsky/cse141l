import random

from bitstring import BitArray


class Machine:
    def __init__(self):
        self.acc = BitArray(uint=random.getrandbits(8), length=8)
        self.reg0 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg1 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg2 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg3 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg4 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg5 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg6 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg7 = BitArray(uint=random.getrandbits(8), length=8)

        self.zero_flag = BitArray(uint=random.getrandbits(1), length=1)
        self.sign_flag = BitArray(uint=random.getrandbits(1), length=1)
        self.carry_flag = BitArray(uint=random.getrandbits(1), length=1)
        self.overflow_flag = BitArray(uint=random.getrandbits(1), length=1)

        self.mem: list[BitArray] = []

        for _ in range(256):
            self.mem.append(BitArray(uint=random.getrandbits(8), length=8))

    def and_R(self, rs: str) -> None:
        """bitwise AND of rs with the accumulator.

        args:
            rs: the register to AND

        notes:
            * clears carry_flag and overflow_flag
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        val = self._get_reg(rs)
        val &= self.acc

        self.zero_flag = BitArray(bin="1") if val.uint == 0 else BitArray(bin="0")
        self.sign_flag = BitArray(bin="1") if val[0] else BitArray(bin="0")
        self.carry_flag = BitArray(bin="0")
        self.overflow_flag = BitArray(bin="0")

        self._set_acc_I(val)

    def xor_R(self, rs: str) -> None:
        """bitwise XOR of rs with the accumulator

        args:
            rs: the register to XOR

        notes:
            * clears carry_flag and overflow_flag
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        val = self._get_reg(rs)
        val ^= self.acc

        self.zero_flag = BitArray(bin="1") if val.uint == 0 else BitArray(bin="0")
        self.sign_flag = BitArray(bin="1") if val[0] else BitArray(bin="0")
        self.carry_flag = BitArray(bin="0")
        self.overflow_flag = BitArray(bin="0")

        self._set_acc_I(val)

    def inv_R(self) -> None:
        """bitwise invert the accumulator.

        notes:
            * preserves flags
        """
        self._set_acc_I(~self.acc)

    def add_R(self, rs: str) -> None:
        """adds the value in rs to the accumulator.

        args:
            rs: the register to add

        Notes:
            * carry_flag: set if there is an unsigned overflow
            * overflow_flag: set if there is a signed overflow (both operands
            same sign, result differs)
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        acc_val = self.acc.uint
        rs_val = self._get_reg(rs).uint
        result = acc_val + rs_val

        self.carry_flag = BitArray(bin="1") if result > 255 else BitArray(bin="0")

        result_wrapped = result % 256

        acc_sign = (acc_val >> 7) & 1
        rs_sign = (rs_val >> 7) & 1
        res_sign = (result_wrapped >> 7) & 1
        signed_overflow = (acc_sign == rs_sign) and (res_sign != acc_sign)
        self.overflow_flag = BitArray(bin="1") if signed_overflow else BitArray(bin="0")

        self.zero_flag = BitArray(bin="1") if result_wrapped == 0 else BitArray(bin="0")
        self.sign_flag = BitArray(bin="1") if res_sign else BitArray(bin="0")

        self._set_acc_I(BitArray(uint=result_wrapped, length=8))

    def sub_R(self, rs: str) -> None:
        """subtracts the value in rs from the accumulator.

        args:
            rs: the register to subtract

        notes:
            * carry_flag: set if there is an unsigned borrow
            * overflow_flag: set if operands have opposite signs and result sign
            differs from acc
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        acc_val = self.acc.uint
        rs_val = self._get_reg(rs).uint
        result = acc_val - rs_val

        result_wrapped = result % 256

        self.carry_flag = BitArray(bin="1") if acc_val < rs_val else BitArray(bin="0")

        acc_sign = (acc_val >> 7) & 1
        rs_sign = (rs_val >> 7) & 1
        res_sign = (result_wrapped >> 7) & 1
        signed_overflow = (acc_sign != rs_sign) and (res_sign != acc_sign)
        self.overflow_flag = BitArray(bin="1") if signed_overflow else BitArray(bin="0")

        self.zero_flag = BitArray(bin="1") if result_wrapped == 0 else BitArray(bin="0")

        self.sign_flag = BitArray(bin="1") if res_sign else BitArray(bin="0")

        self._set_acc_I(BitArray(uint=result_wrapped, length=8))

    def mov_R(self, rs: str) -> None:
        """move the value of rs into the accumulator.

        args:
            rs: the register to move into the accumulator

        notes:
            * preserves flags
        """
        source_reg = self._get_reg(rs)
        self.acc = source_reg

    def sto_R(self, rd: str) -> None:
        """store the accumulator into rd.

        args:
            rd: The register to move acc into

        notes:
            * preserves flags
        """
        self._set_reg(rd)

    def ld_R(self, rs: str) -> None:
        """load from memory into accumulator.

        args:
            rs: the register containing the memory address to load from

        notes:
            * preserves flags
        """
        addr = self._get_reg(rs)
        self._set_acc_I(self.mem[addr.uint].copy())

    def st_R(self, rs: str) -> None:
        """store the accumulator into memory

        args:
            rs: the register containing the memory address to store into

        notes:
            * preserves flags
        """
        addr = self._get_reg(rs)
        self.mem[addr.uint] = self.acc.copy()

    def cmp_R(self, rs: str) -> None:
        """compare the accumulator to a register.

        args:
            rs: the register to compare with

        notes:
            * cmp performs a subtraction and discards the result, but sets flags
            in the same way
            * carry_flag: set if there is an unsigned borrow
            * overflow_flag: set if operands have opposite signs and result sign
              differs from acc
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        acc_val = self.acc.uint
        rs_val = self._get_reg(rs).uint
        result = acc_val - rs_val

        result_wrapped = result % 256

        self.carry_flag = BitArray(bin="1") if acc_val < rs_val else BitArray(bin="0")

        acc_sign = (acc_val >> 7) & 1
        rs_sign = (rs_val >> 7) & 1
        res_sign = (result_wrapped >> 7) & 1
        signed_overflow = (acc_sign != rs_sign) and (res_sign != acc_sign)
        self.overflow_flag = BitArray(bin="1") if signed_overflow else BitArray(bin="0")

        self.zero_flag = BitArray(bin="1") if result_wrapped == 0 else BitArray(bin="0")
        self.sign_flag = BitArray(bin="1") if res_sign else BitArray(bin="0")

    def lsh_I(self, val: BitArray) -> None:
        """performs a logical shift left on the accumulator.

        args:
            val: the number of bits to shift.

        notes:
            * carry_flag: set to the last bit shifted out.
            * overflow_flag: set if the sign bit changed during the shift.
              undefined for shifts > 1.
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        if val.uint < 8 and self.acc[val.uint - 1]:
            self.carry_flag = BitArray(bin="1")
        else:
            self.carry_flag = BitArray(bin="0")
        if val.uint == 1:
            if self.acc[0] == self.acc[1]:
                self.overflow_flag = BitArray(bin="0")
            else:
                self.overflow_flag = BitArray(bin="1")

        result = self.acc << val.uint
        self.zero_flag = BitArray(bin="1") if result.uint == 0 else BitArray(bin="0")
        self.sign_flag = BitArray(bin="1") if result[0] else BitArray(bin="0")

        self._set_acc_I(result)

    def rsh_I(self, val: BitArray) -> None:
        """performs a logical shift right on the accumulator.

        args:
            val: the number of bits to shift.

        notes:
            * carry_flag: set to the last bit shifted out.
            * overflow_flag: set if the sign bit changed during the shift.
              Undefined for shifts > 1.
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        if val.uint < 8 and self.acc[8 - val.uint]:
            self.carry_flag = BitArray(bin="1")
        else:
            self.carry_flag = BitArray(bin="0")
        if val.uint == 1:
            if self.acc[0]:
                self.overflow_flag = BitArray(bin="1")
            else:
                self.overflow_flag = BitArray(bin="0")

        result = self.acc >> val.uint
        self.zero_flag = BitArray(bin="1") if result.uint == 0 else BitArray(bin="0")
        self.sign_flag = BitArray(bin="1") if result[0] else BitArray(bin="0")

        self._set_acc_I(result)

    def ldi_I(self, val: BitArray) -> None:
        """load an immediate into accumulator.

        args:
            val: the value to load into the accumulator

        notes:
            * preserves flags
        """
        self._set_acc_I(val)

    def addi_I(self, val: BitArray) -> None:
        """adds an immediate value to the accumulator.

        args:
            val: the value to add

        notes:
            * carry_flag: set if there is an unsigned overflow
            * overflow_flag: set if there is a signed overflow (both operands
            same sign, result differs)
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        acc_val = self.acc.uint
        imm_val = val.uint
        result = acc_val + imm_val

        self.carry_flag = BitArray(bin="1") if result > 255 else BitArray(bin="0")

        result_wrapped = result % 256

        acc_sign = (acc_val >> 7) & 1
        imm_sign = (imm_val >> 7) & 1
        res_sign = (result_wrapped >> 7) & 1
        signed_overflow = (acc_sign == imm_sign) and (res_sign != acc_sign)
        self.overflow_flag = BitArray(bin="1") if signed_overflow else BitArray(bin="0")

        self.zero_flag = BitArray(bin="1") if result_wrapped == 0 else BitArray(bin="0")
        self.sign_flag = BitArray(bin="1") if res_sign else BitArray(bin="0")

        self._set_acc_I(BitArray(uint=result_wrapped, length=8))

    def subi_I(self, val: BitArray) -> None:
        """subtracts an immediate value from the accumulator.

        args:
            val: the value to subtract

        notes:
            * carry_flag: set if there is an unsigned borrow
            * overflow_flag: set if operands have opposite signs and result sign
            differs from acc
            * zero_flag: set if the result is zero
            * sign_flag: msb of the result
        """
        acc_val = self.acc.uint
        imm_val = val.uint
        result = acc_val - imm_val

        result_wrapped = result % 256

        self.carry_flag = BitArray(bin="1") if acc_val < imm_val else BitArray(bin="0")

        acc_sign = (acc_val >> 7) & 1
        imm_sign = (imm_val >> 7) & 1
        res_sign = (result_wrapped >> 7) & 1
        signed_overflow = (acc_sign != imm_sign) and (res_sign != acc_sign)
        self.overflow_flag = BitArray(bin="1") if signed_overflow else BitArray(bin="0")

        self.zero_flag = BitArray(bin="1") if result_wrapped == 0 else BitArray(bin="0")

        self.sign_flag = BitArray(bin="1") if res_sign else BitArray(bin="0")

        self._set_acc_I(BitArray(uint=result_wrapped, length=8))

    def _get_reg(self, rd: str) -> BitArray:
        match rd:
            case "acc":
                return self.acc.copy()
            case "r0":
                return self.reg0.copy()
            case "r1":
                return self.reg1.copy()
            case "r2":
                return self.reg2.copy()
            case "r3":
                return self.reg3.copy()
            case "r4":
                return self.reg4.copy()
            case "r5":
                return self.reg5.copy()
            case "r6":
                return self.reg6.copy()
            case "r7":
                return self.reg7.copy()
            case _:
                raise ValueError(f"Register {rd} not a valid register name")

    def _set_acc_R(self, rs: str) -> None:
        match rs:
            case "r0":
                self.acc = self.reg0.copy()
            case "r1":
                self.acc = self.reg1.copy()
            case "r2":
                self.acc = self.reg2.copy()
            case "r3":
                self.acc = self.reg3.copy()
            case "r4":
                self.acc = self.reg4.copy()
            case "r5":
                self.acc = self.reg5.copy()
            case "r6":
                self.acc = self.reg6.copy()
            case "r7":
                self.acc = self.reg7.copy()
            case _:
                raise ValueError(f"Register {rs} not a valid register name")

    def _set_acc_I(self, val: BitArray) -> None:
        if len(val) != 8:
            raise ValueError("Immediate values must have width=8")
        self.acc = val.copy()

    def _set_reg(self, rd: str) -> None:
        val = self.acc.copy()
        match rd:
            case "r0":
                self.reg0 = val
            case "r1":
                self.reg1 = val
            case "r2":
                self.reg2 = val
            case "r3":
                self.reg3 = val
            case "r4":
                self.reg4 = val
            case "r5":
                self.reg5 = val
            case "r6":
                self.reg6 = val
            case "r7":
                self.reg7 = val
            case _:
                raise ValueError(f"Register {rd} not a valid register name")
