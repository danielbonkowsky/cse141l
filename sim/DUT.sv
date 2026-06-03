// DUT.sv — CSE141L processor for testbench compatibility
// Interface: clk / start (reset-when-high) / done
// Data memory: dat_mem instance 'dm' with lowercase 'core' for testbench access
// Instruction ROM: loaded from "mach_code.txt" via $readmemb
//
// Full ISA  (9-bit instructions, 8-bit datapath):
//   R/I-type [0|opc(4)|reg/imm(4)]:
//     0x0 AND  0x1 XOR  0x2 INV  0x3 ADD  0x4 SUB
//     0x5 MOV  0x6 STO  0x7 LD   0x8 ST   0x9 CMP
//     0xA JMP  0xB SHF  0xC LDI  0xD ADDI
//   B-type  [1|cond(2)|offset(6)]:
//     00=BEQ  01=BNE  10=BLT(S≠V)  11=BLTU(C)
//   done = 9'b100000000 (beq offset=0, halt)
//
// Flag update rules (matches Python util.py reference):
//   AND/XOR : update Z,S  and  clear C,V
//   ADD/SUB/CMP/ADDI : update Z,S,C,V
//   SHF     : update Z,S only  (preserve C,V)
//   INV/MOV/STO/LD/ST/LDI/JMP : preserve all flags

`timescale 1ns/1ps
module DUT(
  input  clk,
         start,
  output logic done
);

  // ── Instruction memory ──────────────────────────────────────────────────
  logic [8:0] inst_mem[256];
  initial $readmemb("mach_code.txt", inst_mem);

  // ── Data memory ─────────────────────────────────────────────────────────
  logic       wen;
  logic [7:0] dm_addr, dm_in, dm_out;
  dat_mem dm(.clk, .wen, .addr(dm_addr), .dat_in(dm_in), .dat_out(dm_out));

  // ── Processor state ─────────────────────────────────────────────────────
  logic [8:0] pc;
  logic [7:0] acc;
  logic [7:0] reg_file[16];   // r0 hardwired to 0
  logic       zero_f, sign_f, carry_f, ovfl_f;

  // ── Instruction decode ───────────────────────────────────────────────────
  logic [8:0] ir;
  logic       is_branch;
  logic [3:0] opc, reg_imm;
  logic [1:0] cond;
  logic [5:0] boffset;

  assign ir        = inst_mem[pc];
  assign is_branch = ir[8];
  assign opc       = ir[7:4];
  assign reg_imm   = ir[3:0];
  assign cond      = ir[7:6];
  assign boffset   = ir[5:0];

  // r0 hardwired to 0
  logic [7:0] rn;
  assign rn = (reg_imm == 4'd0) ? 8'd0 : reg_file[reg_imm];

  // ── ALU ─────────────────────────────────────────────────────────────────
  // Precompute extended results combinationally
  logic [8:0] add_ext, sub_ext, addi_ext;
  assign add_ext  = {1'b0, acc} + {1'b0, rn};
  assign sub_ext  = {1'b0, acc} - {1'b0, rn};
  assign addi_ext = {1'b0, acc} + {{5{reg_imm[3]}}, reg_imm};

  // SHF shift amount: positive → left, negative → right
  logic [3:0] shamt;
  assign shamt = reg_imm[3] ? (4'd0 - reg_imm) : {1'b0, reg_imm[2:0]};

  logic [7:0] alu_out;
  always_comb begin
    alu_out = 8'd0;
    if (!is_branch) begin
      case (opc)
        4'h0: alu_out = acc & rn;                                      // AND
        4'h1: alu_out = acc ^ rn;                                      // XOR
        4'h2: alu_out = ~acc;                                          // INV
        4'h3: alu_out = add_ext[7:0];                                  // ADD
        4'h4: alu_out = sub_ext[7:0];                                  // SUB
        4'h5: alu_out = rn;                                            // MOV
        4'h6: alu_out = acc;                                           // STO (acc unchanged)
        4'h7: alu_out = dm_out;                                        // LD
        4'h8: alu_out = acc;                                           // ST  (acc unchanged)
        4'h9: alu_out = sub_ext[7:0];                                  // CMP (result discarded)
        4'hA: alu_out = acc;                                           // JMP
        4'hB: alu_out = reg_imm[3] ? (acc >> shamt) : (acc << shamt); // SHF
        4'hC: alu_out = {4'b0, reg_imm};                              // LDI  0..15
        4'hD: alu_out = addi_ext[7:0];                                // ADDI ±8
        default: alu_out = 8'd0;
      endcase
    end
  end

  // ── Flag control ─────────────────────────────────────────────────────────
  // Which instructions update which flag groups
  logic upd_zs;   // update zero + sign
  logic upd_co;   // update carry + overflow (full arithmetic result)
  logic clr_co;   // clear carry + overflow (AND, XOR)

  always_comb begin
    upd_zs = 1'b0; upd_co = 1'b0; clr_co = 1'b0;
    if (!is_branch) begin
      case (opc)
        4'h0: begin upd_zs = 1; clr_co = 1; end  // AND: set Z,S; clear C,V
        4'h1: begin upd_zs = 1; clr_co = 1; end  // XOR: set Z,S; clear C,V
        4'h3: begin upd_zs = 1; upd_co = 1; end  // ADD
        4'h4: begin upd_zs = 1; upd_co = 1; end  // SUB
        4'h9: begin upd_zs = 1; upd_co = 1; end  // CMP
        4'hB:       upd_zs = 1;                   // SHF: Z,S only
        4'hD: begin upd_zs = 1; upd_co = 1; end  // ADDI
        // 0x2 INV, 0x5 MOV, 0x6 STO, 0x7 LD, 0x8 ST, 0xC LDI, 0xA JMP: preserve all
      endcase
    end
  end

  // Computed new flag values
  logic nz, ns, nc, nv;
  assign nz = (alu_out == 8'd0);
  assign ns = alu_out[7];
  assign nc = upd_co ? (opc == 4'h3 ? add_ext[8] : sub_ext[8]) : carry_f;
  assign nv = upd_co ? (opc == 4'h3
                        ? ((acc[7] == rn[7]) & (add_ext[7] != acc[7]))
                        : ((acc[7] != rn[7]) & (sub_ext[7] != acc[7])))
                     : ovfl_f;

  // ── Data memory interface ─────────────────────────────────────────────────
  assign dm_addr = rn;
  assign dm_in   = acc;
  assign wen     = !is_branch && (opc == 4'h8) && !start;

  // ── Branch / jump ────────────────────────────────────────────────────────
  logic branch_taken;
  logic [8:0] branch_target;
  assign branch_target = pc + {{3{boffset[5]}}, boffset};

  always_comb begin
    branch_taken = 1'b0;
    if (is_branch) begin
      case (cond)
        2'b00: branch_taken = zero_f;
        2'b01: branch_taken = ~zero_f;
        2'b10: branch_taken = (sign_f ^ ovfl_f);  // BLT: S≠V
        2'b11: branch_taken = carry_f;
      endcase
    end else if (opc == 4'hA) begin  // JMP absolute
      branch_taken = 1'b1;
    end
  end

  // ── Next PC ──────────────────────────────────────────────────────────────
  logic [8:0] next_pc;
  always_comb begin
    if (start)
      next_pc = 9'd0;
    else if (is_branch && branch_taken)
      next_pc = branch_target;
    else if (!is_branch && opc == 4'hA)
      next_pc = {1'b0, rn};
    else
      next_pc = pc + 9'd1;
  end

  // ── Done signal ──────────────────────────────────────────────────────────
  assign done = (ir == 9'b100000000) && !start;

  // ── Sequential logic ─────────────────────────────────────────────────────
  always_ff @(posedge clk) begin
    if (start) begin
      pc      <= 9'd0;
      acc     <= 8'd0;
      zero_f  <= 1'b0;
      sign_f  <= 1'b0;
      carry_f <= 1'b0;
      ovfl_f  <= 1'b0;
    end else if (!done) begin
      pc <= next_pc;

      // Flag updates
      if (upd_zs) begin zero_f <= nz; sign_f  <= ns; end
      if (upd_co) begin carry_f <= nc; ovfl_f <= nv;  end
      if (clr_co) begin carry_f <= 1'b0; ovfl_f <= 1'b0; end

      // Accumulator write (STO, ST, JMP, CMP skip)
      if (!is_branch) begin
        case (opc)
          4'h6: ;   // STO — write reg, not acc
          4'h8: ;   // ST  — write mem, not acc
          4'hA: ;   // JMP
          4'h9: ;   // CMP — flags only
          default: acc <= alu_out;
        endcase
      end

      // Register file write: STO rN
      if (!is_branch && opc == 4'h6 && reg_imm != 4'd0)
        reg_file[reg_imm] <= acc;
    end
  end

endmodule
