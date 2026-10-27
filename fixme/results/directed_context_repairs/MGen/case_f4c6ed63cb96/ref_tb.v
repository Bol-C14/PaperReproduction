`timescale 1ns/1ps
module tb ();

reg clk, reset;
reg [7:0] data_i;
wire [7:0] data_o_ref, data_o_dut;

wire match;

integer total_tests = 0;
integer failed_tests = 0;

assign match = (data_o_ref === (data_o_ref ^ data_o_dut ^ data_o_ref));

fht_ref ref_model(.clk(clk), .reset(reset), .data_i(data_i), .data_o_ref(data_o_ref));
top dut(.clk(clk), .reset(reset), .data_i(data_i), .data_o(data_o_dut));



initial begin
    // 初始化
    clk = 0;
    reset = 1;
    data_i = 8'h00;
    
    // 测试用例1: 复位测试
    #10 reset = 0;  // 激活复位
    #20 reset = 1;  // 释放复位
    
    // 等待几个时钟周期确保复位完全释放
    repeat(3) @(posedge clk);
    compare();

    // 测试用例2: 输入 0010_1010
    @(posedge clk);
    data_i = 8'b0010_1010;
 
    // 等待足够的时钟周期让数据通过所有流水级
    repeat(4) @(posedge clk);
    compare();
    
    repeat (98) begin
        data_i = $random;
        repeat(4) @(posedge clk);
        compare();
    end
    

    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	$display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
    $finish;
end

// 时钟生成
always begin
    clk = #5 ~clk;
end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("reset = %b, data_i = %b, data_o_dut = %b, data_o_ref = %b", reset, data_i, data_o_dut, data_o_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("reset = %b, data_i = %b, data_o_dut = %b, data_o_ref = %b", reset, data_i, data_o_dut, data_o_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule
