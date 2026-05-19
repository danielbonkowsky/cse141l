module program_counter (
    input  logic        clk,
    input  logic        start,
    input  logic        z_flag,
    input  logic        s_flag,
    input  logic        c_flag,     // ← added for BCS
    input  logic [8:0]  instr,
    input  logic [7:0]  reg_out,
    output logic        done,
    output logic [7:0]  pc
);

    logic [1:0] type_bits;
    logic [1:0] branch_cond;  // condition code within branch
    logic [5:0] branch_offset;
    logic [7:0] branch_offset_sext;

    assign type_bits     = instr[8:7];
    assign branch_cond   = instr[7:6]; // used when type_bit[8]=1
    assign branch_offset = instr[5:0];

    // sign extend 6-bit offset to 8-bit
    assign branch_offset_sext = {{2{branch_offset[5]}}, branch_offset};

    // done flag: beq 0 (1_00_000000)
    assign done = (instr[8] == 1'b1 && 
                   instr[7:6] == 2'b00 && 
                   instr[5:0] == 6'b0) && !start;

    always_ff @(posedge clk) begin
        if (start) begin
            pc <= 8'b0;
        end else begin
            if (instr[8] == 1'b1) begin // branch instruction
                case (instr[7:6]) // condition code
                    2'b00: begin // BEQ
                        if (instr[5:0] == 6'b0) begin
                            pc <= pc; // done, halt
                        end else if (z_flag) begin
                            pc <= pc + branch_offset_sext;
                        end else begin
                            pc <= pc + 1;
                        end
                    end
                    2'b01: begin // BLT
                        if (s_flag) pc <= pc + branch_offset_sext;
                        else        pc <= pc + 1;
                    end
                    2'b10: begin // BCS
                        if (c_flag) pc <= pc + branch_offset_sext;
                        else        pc <= pc + 1;
                    end
                    2'b11: begin // free slot — treat as NOP branch
                        pc <= pc + 1;
                    end
                endcase
            end else begin // R-type or I-type
                if (type_bits == 2'b00 && instr[6:3] == 4'b1010) begin
                    pc <= pc + reg_out; // JMP
                end else begin
                    pc <= pc + 1;
                end
            end
        end
    end

endmodule
