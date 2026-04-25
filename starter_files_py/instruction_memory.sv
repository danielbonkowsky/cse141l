module instruction_memory (
    input  logic [7:0] pc,
    output logic [8:0] instr
);
    logic [8:0] mem [0:255]; // 256 x 9-bit ROM

    // program loaded here at synthesis time
    initial begin
        $readmemb("program.mem", mem);
    end

    assign instr = mem[pc];

endmodule