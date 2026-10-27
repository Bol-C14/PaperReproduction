`timescale 1ns/1ps
/*
 * Copyright 2013, Homer Hsing <homer.hsing@gmail.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* "is_last" == 0 means byte number is 8, no matter what value "byte_num" is. */
/* if "in_ready" == 0, then "is_last" should be 0. */
/* the user switch to next "in" only if "ack" == 1. */

`define low_pos(w,b)      ((w)*64 + (b)*8)
`define low_pos2(w,b)     `low_pos(w,7-b)
`define high_pos(w,b)     (`low_pos(w,b) + 7)
`define high_pos2(w,b)    (`low_pos2(w,b) + 7)

module ref_keccak(clk, reset, in, in_ready, is_last, byte_num,ref_buffer_full, ref_out, ref_out_ready);
    input              clk, reset;
    input      [63:0]  in;
    input              in_ready, is_last;
    input      [2:0]   byte_num;
    output             ref_buffer_full; /* to "user" module */
    output     [511:0] ref_out;
    output reg         ref_out_ready;

    reg                state;     /* state == 0: user will send more input data
                                   * state == 1: user will not send any data */
    wire       [575:0] padder_out,
                       padder_out_1; /* before reorder byte */
    wire               padder_out_ready;
    wire               f_ack;
    wire      [1599:0] f_out;
    wire               f_out_ready;
    wire       [511:0] out1;      /* before reorder byte */
    reg        [10:0]  i;         /* gen "out_ready" */
    genvar w, b;

    assign out1 = f_out[1599:1599-511];

    always @ (posedge clk)
      if (reset)
        i <= 0;
      else
        i <= {i[9:0], state & f_ack};

    always @ (posedge clk)
      if (reset)
        state <= 0;
      else if (is_last)
        state <= 1;

    /* reorder byte ~ ~ */
    generate
      for(w=0; w<8; w=w+1)
        begin : L0
          for(b=0; b<8; b=b+1)
            begin : L1
              assign ref_out[`high_pos(w,b):`low_pos(w,b)] = out1[`high_pos2(w,b):`low_pos2(w,b)];
            end
        end
    endgenerate

    generate
      for(w=0; w<9; w=w+1)
        begin : L2
          for(b=0; b<8; b=b+1)
            begin : L3
              assign padder_out[`high_pos(w,b):`low_pos(w,b)] = padder_out_1[`high_pos2(w,b):`low_pos2(w,b)];
            end
        end
    endgenerate

    always @ (posedge clk)
      if (reset)
        ref_out_ready <= 0;
      else if (i[10])
        ref_out_ready <= 1;

    ref_padder
      padder_ (clk, reset, in, in_ready, is_last, byte_num, ref_buffer_full, padder_out_1, padder_out_ready, f_ack);

    ref_f_permutation
      ref_f_permutation_ (clk, reset, padder_out, padder_out_ready, f_ack, f_out, f_out_ready);
endmodule

`undef low_pos
`undef low_pos2
`undef high_pos
`undef high_pos2


module ref_padder(clk, reset, in, in_ready, is_last, byte_num, ref_buffer_full, ref_out, ref_out_ready, ref_f_ack);
    input              clk, reset;
    input      [63:0]  in;
    input              in_ready, is_last;
    input      [2:0]   byte_num;
    output             ref_buffer_full; /* to "user" module */
    output reg [575:0] ref_out;         /* to "f_permutation" module */
    output             ref_out_ready;   /* to "f_permutation" module */
    input              ref_f_ack;       /* from "f_permutation" module */
    
    reg                state;       /* state == 0: user will send more input data
                                     * state == 1: user will not send any data */
    reg                done;        /* == 1: out_ready should be 0 */
    reg        [8:0]   i;           /* length of "out" buffer */
    wire       [63:0]  v0;          /* output of module "ref_padder1" */
    reg        [63:0]  v1;          /* to be shifted into register "out" */
    wire               accept,      /* accept user input? */
                       update;
    
    assign ref_buffer_full = i[8];
    assign ref_out_ready = ref_buffer_full;
    assign accept = (~ state) & in_ready & (~ ref_buffer_full); // if state == 1, do not eat input
    assign update = (accept | (state & (~ ref_buffer_full))) & (~ done); // don't fill buffer if done

    always @ (posedge clk)
      if (reset)
        ref_out <= 0;
      else if (update)
        ref_out <= {ref_out[575-64:0], v1};

    always @ (posedge clk)
      if (reset)
        i <= 0;
      else if (ref_f_ack | update)
        i <= {i[7:0], 1'b1} & {9{~ ref_f_ack}};
/*    if (ref_f_ack)  i <= 0; */
/*    if (update) i <= {i[7:0], 1'b1}; // increase length */

    always @ (posedge clk)
      if (reset)
        state <= 0;
      else if (is_last)
        state <= 1;

    always @ (posedge clk)
      if (reset)
        done <= 0;
      else if (state & ref_out_ready)
        done <= 1;

    ref_padder1 p0 (in, byte_num, v0);
    
    always @ (*)
      begin
        if (state)
          begin
            v1 = 0;
            v1[7] = v1[7] | i[7]; /* "v1[7]" is the MSB of its last byte */
          end
        else if (is_last == 0)
          v1 = in;
        else
          begin
            v1 = v0;
            v1[7] = v1[7] | i[7];
          end
      end
endmodule


module ref_padder1(in, byte_num, ref_out);
    input      [63:0] in;
    input      [2:0]  byte_num;
    output reg [63:0] ref_out;
    always @ (*)
      case (byte_num)
        0: ref_out =             64'h0100000000000000;
        1: ref_out = {in[63:56], 56'h01000000000000};
        2: ref_out = {in[63:48], 48'h010000000000};
        3: ref_out = {in[63:40], 40'h0100000000};
        4: ref_out = {in[63:32], 32'h01000000};
        5: ref_out = {in[63:24], 24'h010000};
        6: ref_out = {in[63:16], 16'h0100};
        7: ref_out = {in[63:8],   8'h01};
      endcase
endmodule


module ref_rconst2in1(i, ref_rc1, ref_rc2);
    input  [11:0] i;
    output [63:0] ref_rc1, ref_rc2;
    reg    [63:0] ref_rc1, ref_rc2;
    
    always @ (i)
      begin
        ref_rc1 = 0;
        ref_rc1[0] = i[0] | i[2] | i[3] | i[5] | i[6] | i[7] | i[10] | i[11];
        ref_rc1[1] = i[1] | i[2] | i[4] | i[6] | i[8] | i[9];
        ref_rc1[3] = i[1] | i[2] | i[4] | i[5] | i[6] | i[7] | i[9];
        ref_rc1[7] = i[1] | i[2] | i[3] | i[4] | i[6] | i[7] | i[10];
        ref_rc1[15] = i[1] | i[2] | i[3] | i[5] | i[6] | i[7] | i[8] | i[9] | i[10];
        ref_rc1[31] = i[3] | i[5] | i[6] | i[10] | i[11];
        ref_rc1[63] = i[1] | i[3] | i[7] | i[8] | i[10];
      end
    
    always @ (i)
      begin
        ref_rc2 = 0;
        ref_rc2[0] = i[2] | i[3] | i[6] | i[7];
        ref_rc2[1] = i[0] | i[5] | i[6] | i[7] | i[9];
        ref_rc2[3] = i[3] | i[4] | i[5] | i[6] | i[9] | i[11];
        ref_rc2[7] = i[0] | i[4] | i[6] | i[8] | i[10];
        ref_rc2[15] = i[0] | i[1] | i[3] | i[7] | i[10] | i[11];
        ref_rc2[31] = i[1] | i[2] | i[5] | i[9] | i[11];
        ref_rc2[63] = i[1] | i[3] | i[6] | i[7] | i[8] | i[9] | i[10] | i[11];
      end
endmodule

module ref_f_permutation(clk, reset, in, in_ready, ref_ack, ref_out, ref_out_ready);
    input               clk, reset;
    input      [575:0]  in;
    input               in_ready;
    output              ref_ack;
    output reg [1599:0] ref_out;
    output reg          ref_out_ready;

    reg        [10:0]   i; /* select round constant */
    wire       [1599:0] round_in, round_out;
    wire       [63:0]   rc1, rc2;
    wire                update;
    wire                accept;
    reg                 calc; /* == 1: calculating rounds */

    assign accept = in_ready & (~ calc); // in_ready & (i == 0)
    
    always @ (posedge clk)
      if (reset) i <= 0;
      else       i <= {i[9:0], accept};
    
    always @ (posedge clk)
      if (reset) calc <= 0;
      else       calc <= (calc & (~ i[10])) | accept;
    
    assign update = calc | accept;

    assign ref_ack = accept;

    always @ (posedge clk)
      if (reset)
        ref_out_ready <= 0;
      else if (accept)
        ref_out_ready <= 0;
      else if (i[10]) // only change at the last round
        ref_out_ready <= 1;

    assign round_in = accept ? {in ^ ref_out[1599:1599-575], ref_out[1599-576:0]} : ref_out;

    ref_rconst2in1
      rconst_ ({i, accept}, rc1, rc2);

    ref_round2in1
      round_ (round_in, rc1, rc2, ref_round_out);

    always @ (posedge clk)
      if (reset)
        ref_out <= 0;
      else if (update)
        ref_out <= ref_round_out;
endmodule

`define low_pos(x,y)        `high_pos(x,y) - 63
`define high_pos(x,y)       1599 - 64*(5*y+x)
`define add_1(x)            (x == 4 ? 0 : x + 1)
`define add_2(x)            (x == 3 ? 0 : x == 4 ? 1 : x + 2)
`define sub_1(x)            (x == 0 ? 4 : x - 1)
`define rot_up(in, n)       {in[63-n:0], in[63:63-n+1]}
`define rot_up_1(in)        {in[62:0], in[63]}

module ref_round2in1(in, round_const_1, round_const_2, out);
    input  [1599:0] in;
    input  [63:0]   round_const_1, round_const_2;
    output [1599:0] out;

    /* "a ~ g" for round 1 */
    wire   [63:0]   a[4:0][4:0];
    wire   [63:0]   b[4:0];
    wire   [63:0]   c[4:0][4:0], d[4:0][4:0], e[4:0][4:0], f[4:0][4:0], g[4:0][4:0];

    /* "aa ~ gg" for round 2 */
    wire   [63:0]   bb[4:0];
    wire   [63:0]   cc[4:0][4:0], dd[4:0][4:0], ee[4:0][4:0], ff[4:0][4:0], gg[4:0][4:0];

    genvar x, y;

    /* assign "a[x][y][z] == in[w(5y+x)+z]" */
    generate
      for(y=0; y<5; y=y+1)
        begin : L0
          for(x=0; x<5; x=x+1)
            begin : L1
              assign a[x][y] = in[`high_pos(x,y) : `low_pos(x,y)];
            end
        end
    endgenerate

    /* calc "b[x] == a[x][0] ^ a[x][1] ^ ... ^ a[x][4]" */
    generate
      for(x=0; x<5; x=x+1)
        begin : L2
          assign b[x] = a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4];
        end
    endgenerate

    /* calc "c == theta(a)" */
    generate
      for(y=0; y<5; y=y+1)
        begin : L3
          for(x=0; x<5; x=x+1)
            begin : L4
              assign c[x][y] = a[x][y] ^ b[`sub_1(x)] ^ `rot_up_1(b[`add_1(x)]);
            end
        end
    endgenerate

    /* calc "d == rho(c)" */
    assign d[0][0] = c[0][0];
    assign d[1][0] = `rot_up_1(c[1][0]);
    assign d[2][0] = `rot_up(c[2][0], 62);
    assign d[3][0] = `rot_up(c[3][0], 28);
    assign d[4][0] = `rot_up(c[4][0], 27);
    assign d[0][1] = `rot_up(c[0][1], 36);
    assign d[1][1] = `rot_up(c[1][1], 44);
    assign d[2][1] = `rot_up(c[2][1], 6);
    assign d[3][1] = `rot_up(c[3][1], 55);
    assign d[4][1] = `rot_up(c[4][1], 20);
    assign d[0][2] = `rot_up(c[0][2], 3);
    assign d[1][2] = `rot_up(c[1][2], 10);
    assign d[2][2] = `rot_up(c[2][2], 43);
    assign d[3][2] = `rot_up(c[3][2], 25);
    assign d[4][2] = `rot_up(c[4][2], 39);
    assign d[0][3] = `rot_up(c[0][3], 41);
    assign d[1][3] = `rot_up(c[1][3], 45);
    assign d[2][3] = `rot_up(c[2][3], 15);
    assign d[3][3] = `rot_up(c[3][3], 21);
    assign d[4][3] = `rot_up(c[4][3], 8);
    assign d[0][4] = `rot_up(c[0][4], 18);
    assign d[1][4] = `rot_up(c[1][4], 2);
    assign d[2][4] = `rot_up(c[2][4], 61);
    assign d[3][4] = `rot_up(c[3][4], 56);
    assign d[4][4] = `rot_up(c[4][4], 14);

    /* calc "e == pi(d)" */
    assign e[0][0] = d[0][0];
    assign e[0][2] = d[1][0];
    assign e[0][4] = d[2][0];
    assign e[0][1] = d[3][0];
    assign e[0][3] = d[4][0];
    assign e[1][3] = d[0][1];
    assign e[1][0] = d[1][1];
    assign e[1][2] = d[2][1];
    assign e[1][4] = d[3][1];
    assign e[1][1] = d[4][1];
    assign e[2][1] = d[0][2];
    assign e[2][3] = d[1][2];
    assign e[2][0] = d[2][2];
    assign e[2][2] = d[3][2];
    assign e[2][4] = d[4][2];
    assign e[3][4] = d[0][3];
    assign e[3][1] = d[1][3];
    assign e[3][3] = d[2][3];
    assign e[3][0] = d[3][3];
    assign e[3][2] = d[4][3];
    assign e[4][2] = d[0][4];
    assign e[4][4] = d[1][4];
    assign e[4][1] = d[2][4];
    assign e[4][3] = d[3][4];
    assign e[4][0] = d[4][4];

    /* calc "f = chi(e)" */
    generate
      for(y=0; y<5; y=y+1)
        begin : L5
          for(x=0; x<5; x=x+1)
            begin : L6
              assign f[x][y] = e[x][y] ^ ((~ e[`add_1(x)][y]) & e[`add_2(x)][y]);
            end
        end
    endgenerate

    /* calc "g = iota(f)" */
    generate
      for(x=0; x<64; x=x+1)
        begin : L60
          if(x==0 || x==1 || x==3 || x==7 || x==15 || x==31 || x==63)
            assign g[0][0][x] = f[0][0][x] ^ round_const_1[x];
          else
            assign g[0][0][x] = f[0][0][x];
        end
    endgenerate
    
    generate
      for(y=0; y<5; y=y+1)
        begin : L7
          for(x=0; x<5; x=x+1)
            begin : L8
              if(x!=0 || y!=0)
                assign g[x][y] = f[x][y];
            end
        end
    endgenerate

    /* round 2 */

    /* calc "bb[x] == g[x][0] ^ g[x][1] ^ ... ^ g[x][4]" */
    generate
      for(x=0; x<5; x=x+1)
        begin : L12
          assign bb[x] = g[x][0] ^ g[x][1] ^ g[x][2] ^ g[x][3] ^ g[x][4];
        end
    endgenerate

    /* calc "cc == theta(g)" */
    generate
      for(y=0; y<5; y=y+1)
        begin : L13
          for(x=0; x<5; x=x+1)
            begin : L14
              assign cc[x][y] = g[x][y] ^ bb[`sub_1(x)] ^ `rot_up_1(bb[`add_1(x)]);
            end
        end
    endgenerate

    /* calc "dd == rho(cc)" */
    assign dd[0][0] = cc[0][0];
    assign dd[1][0] = `rot_up_1(cc[1][0]);
    assign dd[2][0] = `rot_up(cc[2][0], 62);
    assign dd[3][0] = `rot_up(cc[3][0], 28);
    assign dd[4][0] = `rot_up(cc[4][0], 27);
    assign dd[0][1] = `rot_up(cc[0][1], 36);
    assign dd[1][1] = `rot_up(cc[1][1], 44);
    assign dd[2][1] = `rot_up(cc[2][1], 6);
    assign dd[3][1] = `rot_up(cc[3][1], 55);
    assign dd[4][1] = `rot_up(cc[4][1], 20);
    assign dd[0][2] = `rot_up(cc[0][2], 3);
    assign dd[1][2] = `rot_up(cc[1][2], 10);
    assign dd[2][2] = `rot_up(cc[2][2], 43);
    assign dd[3][2] = `rot_up(cc[3][2], 25);
    assign dd[4][2] = `rot_up(cc[4][2], 39);
    assign dd[0][3] = `rot_up(cc[0][3], 41);
    assign dd[1][3] = `rot_up(cc[1][3], 45);
    assign dd[2][3] = `rot_up(cc[2][3], 15);
    assign dd[3][3] = `rot_up(cc[3][3], 21);
    assign dd[4][3] = `rot_up(cc[4][3], 8);
    assign dd[0][4] = `rot_up(cc[0][4], 18);
    assign dd[1][4] = `rot_up(cc[1][4], 2);
    assign dd[2][4] = `rot_up(cc[2][4], 61);
    assign dd[3][4] = `rot_up(cc[3][4], 56);
    assign dd[4][4] = `rot_up(cc[4][4], 14);

    /* calc "ee == pi(dd)" */
    assign ee[0][0] = dd[0][0];
    assign ee[0][2] = dd[1][0];
    assign ee[0][4] = dd[2][0];
    assign ee[0][1] = dd[3][0];
    assign ee[0][3] = dd[4][0];
    assign ee[1][3] = dd[0][1];
    assign ee[1][0] = dd[1][1];
    assign ee[1][2] = dd[2][1];
    assign ee[1][4] = dd[3][1];
    assign ee[1][1] = dd[4][1];
    assign ee[2][1] = dd[0][2];
    assign ee[2][3] = dd[1][2];
    assign ee[2][0] = dd[2][2];
    assign ee[2][2] = dd[3][2];
    assign ee[2][4] = dd[4][2];
    assign ee[3][4] = dd[0][3];
    assign ee[3][1] = dd[1][3];
    assign ee[3][3] = dd[2][3];
    assign ee[3][0] = dd[3][3];
    assign ee[3][2] = dd[4][3];
    assign ee[4][2] = dd[0][4];
    assign ee[4][4] = dd[1][4];
    assign ee[4][1] = dd[2][4];
    assign ee[4][3] = dd[3][4];
    assign ee[4][0] = dd[4][4];

    /* calc "ff = chi(ee)" */
    generate
      for(y=0; y<5; y=y+1)
        begin : L15
          for(x=0; x<5; x=x+1)
            begin : L16
              assign ff[x][y] = ee[x][y] ^ ((~ ee[`add_1(x)][y]) & ee[`add_2(x)][y]);
            end
        end
    endgenerate

    /* calc "gg = iota(ff)" */
    generate
      for(x=0; x<64; x=x+1)
        begin : L160
          if(x==0 || x==1 || x==3 || x==7 || x==15 || x==31 || x==63)
            assign gg[0][0][x] = ff[0][0][x] ^ round_const_2[x];
          else
            assign gg[0][0][x] = ff[0][0][x];
        end
    endgenerate
    
    generate
      for(y=0; y<5; y=y+1)
        begin : L17
          for(x=0; x<5; x=x+1)
            begin : L18
              if(x!=0 || y!=0)
                assign gg[x][y] = ff[x][y];
            end
        end
    endgenerate

    /* assign "out[w(5y+x)+z] == out_var[x][y][z]" */
    generate
      for(y=0; y<5; y=y+1)
        begin : L99
          for(x=0; x<5; x=x+1)
            begin : L100
              assign out[`high_pos(x,y) : `low_pos(x,y)] = gg[x][y];
            end
        end
    endgenerate
endmodule

`undef low_pos
`undef high_pos
`undef add_1
`undef add_2
`undef sub_1
`undef rot_up
`undef rot_up_1

