// selects ALU second operand: register value or immediate
module mux_alu_src (
    input  logic [7:0] reg_out,
    input  logic [7:0] imm_ext,   // zero-extended immediate
    input  logic       sel,        // 0 = reg, 1 = imm
    output logic [7:0] alu_in
);
    assign alu_in = sel ? imm_ext : reg_out;
endmodule

// selects what gets written back to ACC: ALU result or memory data
module mux_acc_src (
    input  logic [7:0] alu_result,
    input  logic [7:0] mem_data,
    input  logic       sel,        // 0 = ALU, 1 = mem (LD)
    output logic [7:0] acc_next
);
    assign acc_next = sel ? mem_data : alu_result;
endmodule