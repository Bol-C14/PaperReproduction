`timescale 1ns/1ps
module oracle_ca_prng(
               input wire           clk,
               input wire           reset_n,
               input wire [31 : 0]  init_pattern_data,
               input wire           load_init_pattern,
               input wire           next_pattern,
               input wire [7 : 0]   update_rule,
               input wire           load_update_rule,
               output wire [31 : 0] prng_data
              );
  parameter [7 : 0] DEFAULT_RULE = 8'b00011110;
  reg [31 : 0] ca_state_reg;
  reg [31 : 0] ca_state_new;
  reg          ca_state_we;
  reg [7 : 0] update_rule_reg;
  reg [31 : 0] tmp_ca_state_new;
  assign prng_data = ca_state_reg;
  always @ (posedge clk)
    begin : reg_update
      if (!reset_n)
        begin
          update_rule_reg <= DEFAULT_RULE;
          ca_state_reg    <= 32'b00000000000000000000000000000000;
        end
      else
        begin
          if (load_update_rule)
            begin
              update_rule_reg <= update_rule;
           end
          if (ca_state_we)
            begin
              ca_state_reg <= ca_state_new;
           end
         end
    end 
  always @*
    begin : ca_state_update
      case({ca_state_reg[31], ca_state_reg[0], ca_state_reg[1]})
        0:
        begin
          tmp_ca_state_new[0] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[0] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[0] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[0] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[0] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[0] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[0] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[0] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[0], ca_state_reg[1], ca_state_reg[2]})
        0:
        begin
          tmp_ca_state_new[1] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[1] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[1] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[1] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[1] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[1] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[1] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[1] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[1], ca_state_reg[2], ca_state_reg[3]})
        0:
        begin
          tmp_ca_state_new[2] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[2] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[2] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[2] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[2] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[2] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[2] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[2] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[2], ca_state_reg[3], ca_state_reg[4]})
        0:
        begin
          tmp_ca_state_new[3] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[3] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[3] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[3] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[3] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[3] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[3] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[3] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[3], ca_state_reg[4], ca_state_reg[5]})
        0:
        begin
          tmp_ca_state_new[4] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[4] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[4] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[4] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[4] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[4] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[4] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[4] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[4], ca_state_reg[5], ca_state_reg[6]})
        0:
        begin
          tmp_ca_state_new[5] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[5] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[5] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[5] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[5] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[5] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[5] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[5] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[5], ca_state_reg[6], ca_state_reg[7]})
        0:
        begin
          tmp_ca_state_new[6] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[6] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[6] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[6] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[6] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[6] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[6] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[6] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[6], ca_state_reg[7], ca_state_reg[8]})
        0:
        begin
          tmp_ca_state_new[7] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[7] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[7] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[7] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[7] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[7] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[7] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[7] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[7], ca_state_reg[8], ca_state_reg[9]})
        0:
        begin
          tmp_ca_state_new[8] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[8] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[8] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[8] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[8] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[8] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[8] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[8] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[8], ca_state_reg[9], ca_state_reg[10]})
        0:
        begin
          tmp_ca_state_new[9] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[9] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[9] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[9] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[9] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[9] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[9] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[9] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[9], ca_state_reg[10], ca_state_reg[11]})
        0:
        begin
          tmp_ca_state_new[10] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[10] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[10] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[10] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[10] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[10] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[10] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[10] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[10], ca_state_reg[11], ca_state_reg[12]})
        0:
        begin
          tmp_ca_state_new[11] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[11] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[11] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[11] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[11] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[11] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[11] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[11] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[11], ca_state_reg[12], ca_state_reg[13]})
        0:
        begin
          tmp_ca_state_new[12] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[12] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[12] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[12] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[12] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[12] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[12] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[12] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[12], ca_state_reg[13], ca_state_reg[14]})
        0:
        begin
          tmp_ca_state_new[13] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[13] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[13] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[13] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[13] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[13] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[13] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[13] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[13], ca_state_reg[14], ca_state_reg[15]})
        0:
        begin
          tmp_ca_state_new[14] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[14] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[14] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[14] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[14] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[14] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[14] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[14] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[14], ca_state_reg[15], ca_state_reg[16]})
        0:
        begin
          tmp_ca_state_new[15] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[15] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[15] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[15] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[15] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[15] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[15] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[15] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[15], ca_state_reg[16], ca_state_reg[17]})
        0:
        begin
          tmp_ca_state_new[16] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[16] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[16] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[16] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[16] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[16] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[16] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[16] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[16], ca_state_reg[17], ca_state_reg[18]})
        0:
        begin
          tmp_ca_state_new[17] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[17] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[17] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[17] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[17] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[17] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[17] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[17] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[17], ca_state_reg[18], ca_state_reg[19]})
        0:
        begin
          tmp_ca_state_new[18] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[18] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[18] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[18] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[18] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[18] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[18] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[18] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[18], ca_state_reg[19], ca_state_reg[20]})
        0:
        begin
          tmp_ca_state_new[19] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[19] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[19] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[19] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[19] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[19] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[19] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[19] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[19], ca_state_reg[20], ca_state_reg[21]})
        0:
        begin
          tmp_ca_state_new[20] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[20] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[20] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[20] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[20] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[20] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[20] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[20] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[20], ca_state_reg[21], ca_state_reg[22]})
        0:
        begin
          tmp_ca_state_new[21] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[21] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[21] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[21] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[21] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[21] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[21] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[21] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[21], ca_state_reg[22], ca_state_reg[23]})
        0:
        begin
          tmp_ca_state_new[22] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[22] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[22] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[22] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[22] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[22] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[22] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[22] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[22], ca_state_reg[23], ca_state_reg[24]})
        0:
        begin
          tmp_ca_state_new[23] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[23] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[23] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[23] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[23] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[23] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[23] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[23] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[23], ca_state_reg[24], ca_state_reg[25]})
        0:
        begin
          tmp_ca_state_new[24] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[24] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[24] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[24] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[24] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[24] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[24] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[24] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[24], ca_state_reg[25], ca_state_reg[26]})
        0:
        begin
          tmp_ca_state_new[25] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[25] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[25] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[25] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[25] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[25] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[25] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[25] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[25], ca_state_reg[26], ca_state_reg[27]})
        0:
        begin
          tmp_ca_state_new[26] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[26] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[26] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[26] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[26] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[26] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[26] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[26] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[26], ca_state_reg[27], ca_state_reg[28]})
        0:
        begin
          tmp_ca_state_new[27] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[27] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[27] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[27] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[27] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[27] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[27] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[27] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[27], ca_state_reg[28], ca_state_reg[29]})
        0:
        begin
          tmp_ca_state_new[28] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[28] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[28] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[28] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[28] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[28] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[28] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[28] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[28], ca_state_reg[29], ca_state_reg[30]})
        0:
        begin
          tmp_ca_state_new[29] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[29] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[29] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[29] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[29] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[29] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[29] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[29] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[29], ca_state_reg[30], ca_state_reg[31]})
        0:
        begin
          tmp_ca_state_new[30] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[30] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[30] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[30] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[30] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[30] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[30] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[30] = update_rule_reg[7];
        end
      endcase 
      case({ca_state_reg[30], ca_state_reg[31], ca_state_reg[0]})
        0:
        begin
          tmp_ca_state_new[31] = update_rule_reg[0];
        end
        1:
        begin
          tmp_ca_state_new[31] = update_rule_reg[1];
        end
        2:
        begin
          tmp_ca_state_new[31] = update_rule_reg[2];
        end
        3:
        begin
          tmp_ca_state_new[31] = update_rule_reg[3];
        end
        4:
        begin
          tmp_ca_state_new[31] = update_rule_reg[4];
        end
        5:
        begin
          tmp_ca_state_new[31] = update_rule_reg[5];
        end
        6:
        begin
          tmp_ca_state_new[31] = update_rule_reg[6];
        end
        7:
        begin
          tmp_ca_state_new[31] = update_rule_reg[7];
        end
      endcase 
      if (load_init_pattern)
        begin
          ca_state_new = init_pattern_data;
        end
      else
        begin
          ca_state_new = tmp_ca_state_new;
        end
      if (load_init_pattern || next_pattern)
        begin
          ca_state_we = 1;
        end
      else
        begin
          ca_state_we = 0;
        end
    end 
endmodule