module top_level (
    input  logic clk,
    input  logic start,
    output logic done
);

    // wires
    logic [7:0]  pc;
    logic [8:0]  instr;
    logic [7:0]  reg_out, acc;
    logic [7:0]  alu_result, mem_data_out;
    logic [7:0]  alu_in, acc_next;
    logic [3:0]  alu_op;
    logic        z_flag, s_flag, c_flag, ov_flag;
    logic        reg_write, acc_write;
    logic        mem_read, mem_write;
    logic        alu_src, is_branch, branch_type;
    logic [3:0]  imm;
    logic [7:0]  imm_ext;

    // zero-extend immediate
    assign imm_ext = {4'b0000, imm};

    // instantiate modules
    program_counter pc_unit (
        .clk        (clk),
        .start      (start),
        .z_flag     (z_flag),
        .s_flag     (s_flag),
        .instr      (instr),
        .reg_out    (reg_out),
        .done       (done),
        .pc         (pc)
    );

    instruction_memory imem (
        .pc         (pc),
        .instr      (instr)
    );

    control_decoder ctrl (
        .instr       (instr),
        .reg_write   (reg_write),
        .acc_write   (acc_write),
        .mem_read    (mem_read),
        .mem_write   (mem_write),
        .alu_op      (alu_op),
        .alu_src     (alu_src),
        .is_branch   (is_branch),
        .branch_type (branch_type),
        .imm         (imm)
    );

    register_file regfile (
        .clk        (clk),
        .reg_addr   (instr[2:0]),
        .reg_write  (reg_write),
        .acc        (acc),
        .reg_out    (reg_out)
    );

    mux_alu_src mux_a (
        .reg_out    (reg_out),
        .imm_ext    (imm_ext),
        .sel        (alu_src),
        .alu_in     (alu_in)
    );

    alu alu_unit (
        .acc        (acc),
        .alu_in     (alu_in),
        .alu_op     (alu_op),
        .result     (alu_result),
        .z_flag     (z_flag),
        .s_flag     (s_flag),
        .c_flag     (c_flag),
        .ov_flag    (ov_flag)
    );

    data_memory dmem (
        .clk        (clk),
        .addr       (reg_out),
        .data_in    (acc),
        .mem_read   (mem_read),
        .mem_write  (mem_write),
        .data_out   (mem_data_out)
    );

    mux_acc_src mux_b (
        .alu_result (alu_result),
        .mem_data   (mem_data_out),
        .sel        (mem_read),
        .acc_next   (acc_next)
    );

    // ACC register
    always_ff @(posedge clk) begin
        if (acc_write) begin
            acc <= acc_next;
        end
    end

endmodule