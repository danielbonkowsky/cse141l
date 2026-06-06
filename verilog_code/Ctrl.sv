module Ctrl(
  input  [8:0]       mach_code,
  output logic [3:0] AluOp,
  output logic [3:0] Ra,
  output logic [3:0] Wd,
  output logic       WenR,
  output logic       WenD,
  output logic       Ldr,
  output logic       ImmSel,
  output logic       FlagWen,
  output logic       IsJmp,
  output logic       IsBranch,
  output logic [1:0] BranchCond
);

  always_comb begin
    // defaults
    AluOp      = 4'b0;
    Ra         = 4'b0;
    Wd         = 4'hF;   // ACC = r15
    WenR       = 1'b0;
    WenD       = 1'b0;
    Ldr        = 1'b0;
    ImmSel     = 1'b0;
    FlagWen    = 1'b0;
    IsJmp      = 1'b0;
    IsBranch   = 1'b0;
    BranchCond = 2'b0;

    if (!mach_code[8]) begin
      // R/I type
      automatic logic [3:0] opc     = mach_code[7:4];
      automatic logic [3:0] reg_imm = mach_code[3:0];

      AluOp = opc;
      Ra    = reg_imm;

      case (opc)
        4'h0: begin WenR = 1; FlagWen = 1; end                  // AND
        4'h1: begin WenR = 1; FlagWen = 1; end                  // XOR
        4'h2: begin WenR = 1;              end                   // INV (preserves flags)
        4'h3: begin WenR = 1; FlagWen = 1; end                  // ADD
        4'h4: begin WenR = 1; FlagWen = 1; end                  // SUB
        4'h5: begin WenR = 1;              end                   // MOV (preserves flags)
        4'h6: begin WenR = 1; Wd = reg_imm; end                 // STO: write Rd, not ACC
        4'h7: begin WenR = 1; Ldr = 1;    end                   // LD (preserves flags)
        4'h8: begin WenD = 1;              end                   // ST (preserves flags)
        4'h9: begin            FlagWen = 1; end                  // CMP (no write, sets flags)
        4'hA: begin IsJmp = 1;             end                   // JMP
        4'hB: begin WenR = 1; ImmSel = 1; FlagWen = 1; end      // SHF
        4'hC: begin WenR = 1; ImmSel = 1; end                   // LDI (preserves flags)
        4'hD: begin WenR = 1; ImmSel = 1; FlagWen = 1; end      // ADDI
        default: ;
      endcase
    end else begin
      // B type
      IsBranch   = 1'b1;
      BranchCond = mach_code[7:6];
    end
  end

endmodule
