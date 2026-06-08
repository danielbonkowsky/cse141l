module alu(
    input  logic [3:0] alu_op,
    input  logic [7:0] acc,
    input  logic [7:0] alu_in,
    output logic [7:0] result,
    output logic       z_flag,
    output logic       s_flag,
    output logic       c_flag,
    output logic       ov_flag
);

    logic [8:0]        sum9;
    logic signed [3:0] shamt;
    logic [3:0]        shamt_mag;

    always_comb begin
        result    = 8'b0;
        c_flag    = 1'b0;
        ov_flag   = 1'b0;
        sum9      = 9'b0;
        shamt     = $signed(alu_in[3:0]);
        shamt_mag = 4'b0;

        case (alu_op)
            4'h0: result = acc & alu_in;        // AND

            4'h1: result = acc ^ alu_in;        // XOR

            4'h2: result = ~acc;                // INV

            4'h3: begin                         // ADD
                sum9    = {1'b0, acc} + {1'b0, alu_in};
                result  = sum9[7:0];
                c_flag  = sum9[8];
                ov_flag = (acc[7] == alu_in[7]) && (result[7] != acc[7]);
            end

            4'h4: begin                         // SUB
                result  = acc - alu_in;
                c_flag  = (acc < alu_in);
                ov_flag = (acc[7] != alu_in[7]) && (result[7] != acc[7]);
            end

            4'h5: result = alu_in;              // MOV: ACC = reg

            4'h6: result = acc;                 // STO: pass ACC for reg write

            4'h7: result = alu_in;              // LD: pass mem data to ACC

            4'h8: result = acc;                 // ST: pass ACC to memory

            4'h9: begin                         // CMP (SUB, discard result)
                result  = acc - alu_in;
                c_flag  = (acc < alu_in);
                ov_flag = (acc[7] != alu_in[7]) && (result[7] != acc[7]);
            end

            4'hA: result = acc;                 // JMP: ALU noop

            4'hB: begin                         // SHF: signed shift
                if (shamt > 0) begin
                    shamt_mag = shamt;                           // 1–7
                    result    = acc << shamt_mag;
                    c_flag    = acc[4'd8 - shamt_mag];           // last bit shifted out left
                    ov_flag   = (shamt_mag == 4'd1) ? (acc[7] ^ acc[6]) : 1'b0;
                end else if (shamt < 0) begin
                    shamt_mag = -shamt;                          // magnitude 1–8
                    result    = acc >> shamt_mag;
                    c_flag    = acc[shamt_mag - 4'd1];           // last bit shifted out right
                    ov_flag   = (shamt_mag == 4'd1) ? acc[7] : 1'b0;
                end else begin
                    result = acc;                                // shift by 0: noop
                end
            end

            4'hC: result = alu_in;              // LDI: ACC = immediate

            4'hD: begin                         // ADDI: ACC += sign-extended immediate
                sum9   = {1'b0, acc} + {1'b0, alu_in};
                result = sum9[7:0];
                // negative immediate uses borrow semantics; positive uses carry
                c_flag  = alu_in[7] ? (acc < (~alu_in + 8'd1)) : sum9[8];
                ov_flag = (acc[7] == alu_in[7]) && (result[7] != acc[7]);
            end

            default: result = 8'b0;
        endcase
    end

    assign z_flag = (result == 8'b0);
    assign s_flag = result[7];

endmodule
