module control_decoder (
    input  logic [8:0] instr,

    // register file controls
    output logic       reg_write,   // STO: write ACC to register
    output logic       acc_write,   // write result back to ACC
    
    // memory controls
    output logic       mem_read,    // LD
    output logic       mem_write,   // ST

    // ALU controls
    output logic [3:0] alu_op,      // operation for ALU
    output logic       alu_src,     // 0 = reg_out, 1 = immediate

    // branch controls
    output logic       is_branch,
    output logic       branch_type, // 0 = BEQ, 1 = BLT

    // immediate
    output logic [3:0] imm          // for I-type
);

    logic [1:0] type_bits;
    logic [3:0] opcode;

    assign type_bits = instr[8:7];
    assign opcode    = instr[6:3];
    assign imm       = instr[3:0];

    always_comb begin
        // defaults
        reg_write   = 0;
        acc_write   = 0;
        mem_read    = 0;
        mem_write   = 0;
        alu_op      = 4'b0000;
        alu_src     = 0;
        is_branch   = 0;
        branch_type = 0;

        case (type_bits)
            2'b00: begin // R-type
                alu_op  = opcode;
                alu_src = 0; // use reg_out
                case (opcode)
                    4'b0000: acc_write = 1; // AND
                    4'b0001: acc_write = 1; // XOR
                    4'b0010: acc_write = 1; // INV
                    4'b0011: acc_write = 1; // ADD
                    4'b0100: acc_write = 1; // SUB
                    4'b0101: acc_write = 1; // MOV
                    4'b0110: reg_write = 1; // STO
                    4'b0111: begin           // LD
                        mem_read  = 1;
                        acc_write = 1;
                    end
                    4'b1000: mem_write  = 1; // ST
                    4'b1001: ;               // CMP — only sets flags
                    4'b1010: ;               // JMP — handled in PC
                    default: ;
                endcase
            end

            2'b01: begin // I-type
                alu_src = 1; // use immediate
                acc_write = 1;
                alu_op = {1'b1, instr[6:4]}; // pass I-type opcode to ALU
            end

            2'b10: begin // BEQ
                is_branch   = 1;
                branch_type = 0;
            end

            2'b11: begin // BLT
                is_branch   = 1;
                branch_type = 1;
            end
        endcase
    end

endmodule