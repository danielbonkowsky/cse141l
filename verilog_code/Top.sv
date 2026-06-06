module Top(
  input  logic Clk,
               Reset,
  output logic Done
);

  // Program counter
  wire [9:0] PC;

  // Instruction
  wire [8:0] mach_code;

  // Control signals
  wire [3:0] AluOp;
  wire [3:0] Ra;
  wire [3:0] Wd;
  wire       WenR, WenD, Ldr, ImmSel, FlagWen, IsJmp, IsBranch;
  wire [1:0] BranchCond;

  // Data paths
  wire [7:0] RdatAcc, RdatReg;   // register file reads
  wire [7:0] DatA, DatB;         // ALU inputs
  wire [7:0] Rslt;                // ALU result
  wire [7:0] Rdat;                // data memory read
  wire [7:0] Wdat;                // register file write data
  wire [7:0] Addr;                // data memory address
  wire [7:0] WdatD;               // data memory write data

  // ALU flags (combinational)
  wire z_flag, s_flag, c_flag, ov_flag;

  // Registered flags (persist between instructions)
  logic z_reg, s_reg, c_reg, ov_reg;

  // Branch / jump control
  logic       branch_taken;
  wire        Jen;
  wire [9:0]  jump_target;

  // Done: the "done" encoding is beq 0 = 9'b100000000
  assign Done = (mach_code == 9'b100000000);

  // Flag registers — only updated by instructions that affect flags
  always_ff @(posedge Clk) begin
    if (FlagWen) begin
      z_reg  <= z_flag;
      s_reg  <= s_flag;
      c_reg  <= c_flag;
      ov_reg <= ov_flag;
    end
  end

  // Branch condition evaluation (reads registered flags)
  always_comb begin
    case (BranchCond)
      2'b00: branch_taken = IsBranch & z_reg;                // BEQ: zero flag
      2'b01: branch_taken = IsBranch & ~z_reg;               // BNE: not zero
      2'b10: branch_taken = IsBranch & (s_reg ^ ov_reg);     // BLT: sign != overflow
      2'b11: branch_taken = IsBranch & c_reg;                // BLTU: carry (borrow)
      default: branch_taken = 1'b0;
    endcase
  end

  // Jump target: absolute (JMP rN) or PC-relative (branches)
  wire signed [9:0] br_offset = {{4{mach_code[5]}}, mach_code[5:0]};
  assign jump_target = IsJmp ? {2'b0, RdatReg} : (PC + 10'd1 + br_offset);
  assign Jen = IsJmp | branch_taken;

  // Immediate extension: zero-extend for LDI, sign-extend for SHF/ADDI
  wire [7:0] imm_ext = (AluOp == 4'hC) ? {4'b0, mach_code[3:0]}
                                        : {{4{mach_code[3]}}, mach_code[3:0]};

  // ALU input B mux: register value or extended immediate
  assign DatA  = RdatAcc;
  assign DatB  = ImmSel ? imm_ext : RdatReg;

  // Register write data: ALU result, or memory data for LD
  assign Wdat  = Ldr ? Rdat : Rslt;

  // Memory address is always the operand register value
  assign Addr  = RdatReg;

  // ST always stores ACC to memory
  assign WdatD = RdatAcc;

  // Module instantiations

  ProgCtr PC1(
    .Clk,
    .Reset,
    .Jen,
    .Jump  (jump_target),
    .PC
  );

  InstROM IR1(
    .PC,
    .mach_code
  );

  Ctrl C1(
    .mach_code,
    .AluOp,
    .Ra,
    .Wd,
    .WenR,
    .WenD,
    .Ldr,
    .ImmSel,
    .FlagWen,
    .IsJmp,
    .IsBranch,
    .BranchCond
  );

  RegFile RF1(
    .Clk,
    .Wen   (WenR),
    .Ra,
    .Wd,
    .Wdat,
    .RdatAcc,
    .RdatReg
  );

  alu A1(
    .alu_op (AluOp),
    .acc    (DatA),
    .alu_in (DatB),
    .result (Rslt),
    .z_flag,
    .s_flag,
    .c_flag,
    .ov_flag
  );

  DMem DM1(
    .Clk,
    .Wen  (WenD),
    .WDat (WdatD),
    .Addr,
    .Rdat
  );

endmodule
