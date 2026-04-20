import random

from bitstring import BitArray


class Machine:
    def __init__(self):
        self.reg1 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg2 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg3 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg4 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg5 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg6 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg7 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg8 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg9 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg10 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg11 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg12 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg13 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg14 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg15 = BitArray(uint=random.getrandbits(8), length=8)
        self.reg16 = BitArray(uint=random.getrandbits(8), length=8)

        self.zero_flag = BitArray(uint=random.getrandbits(1), length=1)
        self.sign_flag = BitArray(uint=random.getrandbits(1), length=1)
        self.carry_flag = BitArray(uint=random.getrandbits(1), length=1)
        self.overflow_flag = BitArray(uint=random.getrandbits(1), length=1)
        self.underflow_flag = BitArray(uint=random.getrandbits(1), length=1)

        self.mem: list[BitArray] = []

        for _ in range(500):
            self.mem.append(BitArray(uint=random.getrandbits(8), length=8))


    def add(self, rd: str, rs1: str, rs2: str) -> None:
        raw_sum = self.get_reg(rs1).uint + self.get_reg(rs2).uint
        overflow = raw_sum >= 256

        self.set_reg(rd, BitArray(uint=raw_sum & 255, length=8))
        if overflow:
            self.carry_flag = BitArray(uint=1, length=8)
        else:
            self.carry_flag = BitArray(uint=0, length=8)


    def and_reg(self, rd: str, rs1: str, rs2: str) -> None:
        self.set_reg(rd, self.get_reg(rs1)&self.get_reg(rs2))


    def asr(self, rd: str, amt: int) -> None:
        val = self.get_reg(rd)
        rightmost = val[-1]
        sign_bit = val[0]
        val >>= amt
        if sign_bit:
            val[:amt] = BitArray(uint=0, length=amt).invert()
        self.set_reg(rd, val)
        if rightmost:
            self.underflow_flag = BitArray(uint=1, length=1)
        else:
            self.underflow_flag = BitArray(uint=0, length=1)

    
    def lsh(self, rd: str, amt: int) -> None:
        val = self.get_reg(rd)
        if val[:amt].uint > 0:
            self.overflow_flag = BitArray(uint=1, length=1)
        else:
            self.overflow_flag = BitArray(uint=0, length=1)
        self.set_reg(rd, val<<2)


    def scmp(self, rs1: str, rs2: str) -> None:
        if self.get_reg(rs1).int < self.get_reg(rs2).int:
            self.sign_flag = BitArray(uint=1, length=1)
        else:
            self.sign_flag = BitArray(uint=0, length=1)
        
        if self.get_reg(rs1).int == self.get_reg(rs2).int:
            self.zero_flag = BitArray(uint=1, length=1)
        else:
            self.zero_flag = BitArray(uint=0, length=1)


    def ucmp(self, rs1: str, rs2: str) -> None:
        if self.get_reg(rs1).uint < self.get_reg(rs2).uint:
            self.sign_flag = BitArray(uint=1, length=1)
        else:
            self.sign_flag = BitArray(uint=0, length=1)
        
        if self.get_reg(rs1).uint == self.get_reg(rs2).uint:
            self.zero_flag = BitArray(uint=1, length=1)
        else:
            self.zero_flag = BitArray(uint=0, length=1)


    def count_ones(self, rd: str, rs: str) -> None:
        cnt = 0
        for bit in self.get_reg(rs).bin:
            cnt += int(bit)
        self.set_reg(rd, BitArray(uint=cnt, length=8))


    def xor(self, rd: str, rs1: str, rs2: str) -> None:
       self.set_reg(rd, self.get_reg(rs1)^self.get_reg(rs2))


    def invert_reg(self, rd) -> None:
        val = self.get_reg(rd)
        val.invert()
        self.set_reg(rd, val)


    def set_reg(self, rd: str, val: BitArray) -> None:
        match rd:
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
            case "r8":
                self.reg8 = val
            case "r9":
                self.reg9 = val
            case "r10":
                self.reg10 = val
            case "r11":
                self.reg11 = val
            case "r12":
                self.reg12 = val
            case "r13":
                self.reg13 = val
            case "r14":
                self.reg14 = val
            case "r15":
                self.reg15 = val
            case "r16":
                self.reg16 = val
            case _:
                raise ValueError(f"Register {rd} not a valid register name")


    def get_reg(self, rd: str) -> BitArray:
        match rd:
            case "r1": return self.reg1.copy()
            case "r2": return self.reg2.copy()
            case "r3": return self.reg3.copy()
            case "r4": return self.reg4.copy()
            case "r5": return self.reg5.copy()
            case "r6": return self.reg6.copy()
            case "r7": return self.reg7.copy()
            case "r8": return self.reg8.copy()
            case "r9": return self.reg9.copy()
            case "r10": return self.reg10.copy()
            case "r11": return self.reg11.copy()
            case "r12": return self.reg12.copy()
            case "r13": return self.reg13.copy()
            case "r14": return self.reg14.copy()
            case "r15": return self.reg15.copy()
            case "r16": return self.reg16.copy()
            case _: raise ValueError(f"Register {rd} not a valid register name")


    def set_mem(self, loc: int, rs: str) -> None:
        self.mem[loc] = self.get_reg(rs)


    def get_mem(self, rd: str, loc: int) -> None:
        self.set_reg(rd, self.mem[loc].copy())
