// program_counter.sv
// claude draft

module program_counter (
    input  logic        clk,
    input  logic        rst,        // reset / start signal
    input  logic        start,      // from testbench
    input  logic        z_flag,     // zero flag from ALU
    input  logic        s_flag,     // sign flag from ALU
    input  logic [8:0]  instr,      // full instruction
    input  logic [7:0]  reg_out,    // register value for JMP
    output logic        done,       // done flag to testbench
    output logic [7:0]  pc          // program counter output
);

    // instruction fields
    logic [1:0] type_bits;
    logic [6:0] branch_offset;
    logic [7:0] branch_offset_sext; // sign extended

    assign type_bits     = instr[8:7];
    assign branch_offset = instr[6:0];

    // sign extend 7-bit offset to 8-bit
    assign branch_offset_sext = {{1{branch_offset[6]}}, branch_offset};

    // done flag: beq 0 (10_0000000)
    assign done = (instr == 9'b10_0000000) && !start;

    always_ff @(posedge clk) begin
        if (start) begin
            pc <= 8'b0; // reset PC to 0 on start
        end else begin
            case (type_bits)
                2'b10: begin // BEQ
                    if (instr == 9'b10_0000000) begin
                        pc <= pc; // done, halt
                    end else if (z_flag) begin
                        pc <= pc + branch_offset_sext;
                    end else begin
                        pc <= pc + 1;
                    end
                end
                2'b11: begin // BLT
                    if (s_flag) begin
                        pc <= pc + branch_offset_sext;
                    end else begin
                        pc <= pc + 1;
                    end
                end
                default: begin
                    // R-type or I-type: check for JMP (00_1010_XXX)
                    if (type_bits == 2'b00 && instr[6:3] == 4'b1010) begin
                        pc <= pc + reg_out; // JMP
                    end else begin
                        pc <= pc + 1;
                    end
                end
            endcase
        end
    end

endmodule