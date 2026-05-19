module control_decoder (
    input  logic [8:0] instr,

    output logic       reg_write,
    output logic       acc_write,
    output logic       mem_read,
    output logic       mem_write,
    output logic [3:0] alu_op,
    output logic       alu_src,
    output logic [1:0] branch_cond,  // ← 2-bit now
    output logic [3:0] imm
);

    logic [1:0] type_bits;
    logic [3:0] opcode;

    assign type_bits = instr[8:7];
    assign opcode    = instr[6:3];
    assign imm       = instr[3:0];

    always_comb begin
        reg_write   = 0;
        acc_write   = 0;
        mem_read    = 0;
        mem_write   = 0;
        alu_op      = 4'b0000;
        alu_src     = 0;
        branch_cond = 2'b00;

        if (instr[8] == 1'b1) begin // branch
            branch_cond = instr[7:6];
        end else begin
            case (type_bits)
                2'b00: begin // R-type
                    alu_op  = opcode;
                    alu_src = 0;
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
                        4'b1000: mem_write = 1;  // ST
                        4'b1001: ;               // CMP
                        4'b1010: ;               // JMP
                        default: ;
                    endcase
                end

                2'b01: begin // I-type
                    alu_src   = 1;
                    acc_write = 1;
                    // map I-type 3-bit opcode to ALU op
                    // SHF=000, LDI=001, ADDI=010
                    case (instr[6:4])
                        3'b000: alu_op = 4'b1011; // SHF
                        3'b001: alu_op = 4'b1101; // LDI
                        3'b010: alu_op = 4'b1110; // ADDI
                        default: alu_op = 4'b0000;
                    endcase
                end

                default: ; // branches handled above
            endcase
        end
    end

endmodule
