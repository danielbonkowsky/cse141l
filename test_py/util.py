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
        self.underflow_flag = BitArray(uint=random.getrandbits(1), length=1)

        self.mem: list[BitArray] = []

        for _ in range(500):
            self.mem.append(BitArray(uint=random.getrandbits(8), length=8))

    def and_R(self, rs: str) -> None:
        """bitwise and with accumulator"""
        val = self._get_reg(rs)
        val &= self.acc
        self._set_acc_I(val)

    def xor_R(self, rs: str) -> None:
        """bitwise exclusive or with accumulator"""
        val = self._get_reg(rs)
        val ^= self.acc
        self._set_acc_I(val)

    def inv_R(self) -> None:
        """bitwise invert accumulator"""
        self._set_acc_I(~self.acc)

    def add_R(self, rs: str) -> None:
        """add register to accumulator"""
        acc_val = self.acc.uint
        rs_val = self._get_reg(rs).uint
        if acc_val + rs_val > 255:
            self.carry_flag = BitArray(bin="1")
        else:
            self.carry_flag = BitArray(bin="0")
        self._set_acc_I(BitArray(uint=(acc_val + rs_val) % 256, length=8))

    def sub_R(self, rs: str) -> None:
        """subtract register from accumulator"""
        rs_val = self._get_reg(rs)
        rs_val = ~rs_val
        rs_val = BitArray(uint=(rs_val.uint + 1) % 256, length=8)
        acc_val = self.acc.uint
        self._set_acc_I(BitArray(uint=(acc_val + rs_val.uint) % 256, length=8))

    def mov_R(self, rs: str) -> None:
        """move register into accumulator"""
        source_reg = self._get_reg(rs)
        self.acc = source_reg

    def sto_R(self, rd: str) -> None:
        """store accumulator into register"""
        self._set_reg(rd)

    def ld_R(self, rs: str) -> None:
        """load from memory into accumulator"""
        addr = self._get_reg(rs)
        self._set_acc_I(self.mem[addr.uint].copy())

    def st_R(self, rs: str) -> None:
        """store accumulator into memory"""
        addr = self._get_reg(rs)
        self.mem[addr.uint] = self.acc.copy()

    def cmp_R(self, rs: str) -> None:
        """compare accumulator to register"""
        rs_val = self._get_reg(rs)
        self.zero_flag = BitArray(bin="0")
        self.sign_flag = BitArray(bin="0")

        if rs_val.int == self.acc.int:
            self.zero_flag = BitArray(bin="1")
        if self.acc.int < rs_val.int:
            self.sign_flag = BitArray(bin="1")

    def lsh_I(self, val: BitArray) -> None:
        """logical shift left accumulator"""
        if self.acc[0]:
            self.overflow_flag = BitArray(bin="1")
        else:
            self.overflow_flag = BitArray(bin="0")

        self._set_acc_I(self.acc << val.uint)

    def rsh_I(self, val: BitArray) -> None:
        """logical shift right accumulator"""
        self._set_acc_I(self.acc >> val.uint)

    def ldi_I(self, val: BitArray) -> None:
        """load immediate into accumulator"""
        self._set_acc_I(val)

    def addi_I(self, val: BitArray) -> None:
        """add immediate to accumulator"""
        acc_val = self.acc.uint
        i_val = val.uint
        if acc_val + i_val > 255:
            self.overflow_flag = BitArray(bin="1")
        else:
            self.overflow_flag = BitArray(bin="0")
        self._set_acc_I(BitArray(uint=(acc_val + i_val) % 256, length=8))

    def subi_I(self, val: BitArray) -> None:
        """subtract immediate from accumulator"""
        i_val = ~val
        i_val = BitArray(uint=(i_val.uint + 1) % 256, length=8)
        acc_val = self.acc.uint
        self._set_acc_I(BitArray(uint=(acc_val + i_val.uint) % 256, length=8))

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
