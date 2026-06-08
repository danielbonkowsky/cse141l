# Simulation and Synthesis Instruction
## Simulation
This section will explain how to run the testbenches on our code in EDA Playground. In addition to the code we submitted on Gradescope, you can find a runnable version of our code on [EDA Playground](https://www.edaplayground.com/x/ShAL).

### Program 1
1. In `InstrROM.sv`, change line 9 to `$readmemb("program1.mem",Core);` so the correct code is loaded into memory
2. In `testbench.sv`, change line 3 to `` `include "program1_tb.sv"`` to run the correct testbench
3. Select Siemens Questa 2025.2 under Tools & Simulators
4. Save and run the code. The log will show that all tests pass

### Program 2
1. In `InstrROM.sv`, change line 9 to `$readmemb("program2.mem",Core);` so the correct code is loaded into memory
2. In `testbench.sv`, change line 3 to `` `include "program2_tb.sv"`` to run the correct testbench
3. Select Siemens Questa 2025.2 under Tools & Simulators
4. Save and run the code. The log will show that all tests pass

### Program 3
1. In `InstrROM.sv`, change line 9 to `$readmemb("program3.mem",Core);` so the correct code is loaded into memory
2. In `testbench.sv`, change line 3 to `` `include "program3_tb.sv"`` to run the correct testbench
3. Select Siemens Questa 2025.2 under Tools & Simulators
4. Save and run the code. The log will show that all tests pass

## Synthesis
This section will explain how to synthesize netlists for our processor in EDA Playground. As before, you can find our code [here](https://www.edaplayground.com/x/ShAL).

1. Under Tools & Simulators, select Siemens Precision 2024.2
2. Select "Show **netlist** after run"
3. Save and run the code; eventually, a netlist will open up in a new browser window
