// muxes.sv
// DelicateArch multiplexers
// Two muxes in the datapath: mux_alu_src and mux_acc_src

// -----------------------------------------------------------------------------
// mux_alu_src
// Selects the ALU's second operand.
//   sel = 0 (R-type): pass register file output
//   sel = 1 (I-type): pass sign-extended 4-bit immediate
// Note: sign extension of the 4-bit immediate is handled in top_level.sv
//       before being passed in as imm_ext.
// -----------------------------------------------------------------------------
module mux_alu_src (
    input  logic [7:0] reg_out,   // value from register file
    input  logic [7:0] imm_ext,   // sign-extended 4-bit immediate
    input  logic       sel,        // 0 = register, 1 = immediate
    output logic [7:0] alu_in
);
    assign alu_in = sel ? imm_ext : reg_out;
endmodule


// -----------------------------------------------------------------------------
// mux_acc_src
// Selects what value gets written back to the accumulator.
//   sel = 0 (all non-LD instructions): pass ALU result
//   sel = 1 (LD instruction):          pass data memory output
// -----------------------------------------------------------------------------
module mux_acc_src (
    input  logic [7:0] alu_result,  // result from ALU
    input  logic [7:0] mem_data,    // data read from data memory
    input  logic       sel,          // 0 = ALU result, 1 = memory data (LD)
    output logic [7:0] acc_next
);
    assign acc_next = sel ? mem_data : alu_result;
endmodule
