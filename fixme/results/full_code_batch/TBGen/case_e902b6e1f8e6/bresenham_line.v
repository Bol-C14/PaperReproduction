`timescale 1ns/1ps

module bresenham_line(clk_i, rst_i,
pixel0_x_i, pixel0_y_i, pixel1_x_i, pixel1_y_i, 
draw_line_i, read_pixel_i, 
busy_o, x_major_o, major_o, minor_o, valid_o
);
parameter point_width = 16;
parameter subpixel_width = 16;
input clk_i;
input rst_i;
input signed [point_width-1:-subpixel_width] pixel0_x_i;
input signed [point_width-1:-subpixel_width] pixel1_x_i;
input signed [point_width-1:-subpixel_width] pixel0_y_i;
input signed [point_width-1:-subpixel_width] pixel1_y_i;
input draw_line_i;
input read_pixel_i;
output reg busy_o;
output reg valid_o;
output reg signed [point_width-1:0] major_o;
output reg signed [point_width-1:0] minor_o;
reg [point_width-1:-subpixel_width] xdiff; 
reg [point_width-1:-subpixel_width] ydiff; 
output reg x_major_o; 
reg signed [point_width-1:-subpixel_width] left_pixel_x; 
reg signed [point_width-1:-subpixel_width] left_pixel_y; 
reg signed [point_width-1:-subpixel_width] right_pixel_x; 
reg signed [point_width-1:-subpixel_width] right_pixel_y;
reg [point_width-1:-subpixel_width] delta_major; 
reg [point_width-1:-subpixel_width] delta_minor; 
reg minor_slope_positive; 
reg  signed          [point_width-1:0] major_goal;
reg  signed [2*point_width-1:-subpixel_width] eps;
wire signed [2*point_width-1:-subpixel_width] eps_delta_minor;
wire done;
reg [2:0] state;
parameter wait_state = 0, line_prep_state = 1, line_state = 2, raster_state = 3;
assign eps_delta_minor = eps+delta_minor;
always@(posedge clk_i or posedge rst_i)
if(rst_i)
  state <= wait_state;
else
  case (state)
    wait_state:
      if(draw_line_i)
        state <= line_prep_state; 
    line_prep_state:
      state <= line_state;
    line_state:
      state <= raster_state;
    raster_state:
      if(!busy_o)
        state <= wait_state;
  endcase
wire is_inside_screen = (minor_o >= 0) & (major_o >= -1);
reg previously_outside_screen;
always@(posedge clk_i or posedge rst_i)
begin
  if(rst_i)
  begin
    minor_slope_positive <= 1'b0;
    eps                  <= 1'b0;
    major_o              <= 1'b0;
    minor_o              <= 1'b0;
    busy_o               <= 1'b0;
    major_goal           <= 1'b0;
    x_major_o            <= 1'b0;
    delta_minor          <= 1'b0;
    delta_major          <= 1'b0;
    valid_o              <= 1'b0;
    left_pixel_x         <= 1'b0;
    left_pixel_y         <= 1'b0;
    right_pixel_x        <= 1'b0;
    right_pixel_y        <= 1'b0;
    xdiff                <= 1'b0;
    ydiff                <= 1'b0;
    previously_outside_screen <= 1'b0;
  end
  else
  begin
   case (state)
      wait_state:
        if(draw_line_i)
        begin
          previously_outside_screen <= 1'b0;
          busy_o  <= 1'b1;
          valid_o <= 1'b0;
          if(pixel0_x_i > pixel1_x_i)
          begin
            xdiff         <= pixel0_x_i - pixel1_x_i;
            left_pixel_x  <= pixel1_x_i;
            left_pixel_y  <= pixel1_y_i;
            right_pixel_x <= pixel0_x_i;
            right_pixel_y <= pixel0_y_i;
            if(pixel1_y_i > pixel0_y_i)
            begin
              ydiff                <= pixel1_y_i - pixel0_y_i;
              minor_slope_positive <= 1'b0;
            end
            else
            begin
              ydiff                <= pixel0_y_i - pixel1_y_i;
              minor_slope_positive <= 1'b1;
            end
          end
          else
          begin
            xdiff         <= pixel1_x_i - pixel0_x_i;
            left_pixel_x  <= pixel0_x_i;
            left_pixel_y  <= pixel0_y_i;
            right_pixel_x <= pixel1_x_i;
            right_pixel_y <= pixel1_y_i;
            if(pixel0_y_i > pixel1_y_i)
            begin
              ydiff                <= pixel0_y_i - pixel1_y_i;
              minor_slope_positive <= 1'b0; 
            end
            else
            begin
              ydiff                <= pixel1_y_i - pixel0_y_i;
              minor_slope_positive <= 1'b1; 
            end
          end
        end
      line_prep_state:
      begin
        if(xdiff > ydiff)
        begin 
          x_major_o    <= 1'b1;
          delta_major  <= xdiff;
          delta_minor  <= ydiff;
        end
        else
        begin 
          x_major_o    <= 1'b0;    
          delta_major  <= ydiff;
          delta_minor  <= xdiff; 
        end
      end
      line_state:
      begin
          if(x_major_o) 
          begin
            major_o    <= $signed(left_pixel_x[point_width-1:0]);
            minor_o    <= $signed(left_pixel_y[point_width-1:0]);
            major_goal <= $signed(right_pixel_x[point_width-1:0]);
          end
          else 
          begin
            major_o    <= $signed(left_pixel_y[point_width-1:0]);
            minor_o    <= $signed(left_pixel_x[point_width-1:0]);
            major_goal <= $signed(right_pixel_y[point_width-1:0]);
          end
          eps          <= 1'b0;
          busy_o       <= 1'b1;
          valid_o      <= (left_pixel_x >= 0 && left_pixel_y >= 0);
          previously_outside_screen <= ~(left_pixel_x >= 0 && left_pixel_y >= 0);
      end
    raster_state:
    begin
      valid_o <= (previously_outside_screen | read_pixel_i) & is_inside_screen;
      previously_outside_screen <= ~is_inside_screen;
      if((read_pixel_i & is_inside_screen) | previously_outside_screen)
      begin
        if((major_o < major_goal) & minor_slope_positive & x_major_o & busy_o) 
        begin
          major_o   <=  major_o + 1'b1; 
          if((eps_delta_minor*2) >= $signed(delta_major))
          begin
            eps     <=  eps_delta_minor - delta_major;
            minor_o <=  minor_o + 1'b1; 
          end
          else
            eps     <=  eps_delta_minor;
        end
        else if((major_o < major_goal) & minor_slope_positive & !x_major_o & busy_o) 
        begin
          major_o   <=  major_o + 1'b1; 
          if((eps_delta_minor*2) >= $signed(delta_major))
          begin
            eps     <=  eps_delta_minor - delta_major;
            minor_o <=  minor_o + 1'b1; 
          end
          else
            eps     <=  eps_delta_minor;
        end
        else if((major_o > major_goal) & !minor_slope_positive & !x_major_o & busy_o)
        begin
          major_o   <=  major_o - 1'b1; 
          if((eps_delta_minor*2) >= $signed(delta_major))
          begin
            eps     <=  eps_delta_minor - delta_major;
            minor_o <=  minor_o + 1'b1; 
          end
          else
            eps     <=  eps_delta_minor;
        end
        else if((major_o < major_goal) & !minor_slope_positive & x_major_o & busy_o)
        begin
          major_o   <=  major_o + 1'b1; 
          if((eps_delta_minor*2) >= $signed(delta_major))
          begin
            eps     <=  eps_delta_minor - delta_major;
            minor_o <=  minor_o - 1'b1; 
          end
          else
            eps     <=  eps_delta_minor;
        end
        else if(busy_o)
        begin
          busy_o <=  1'b0;
          valid_o <= 1'b0;
        end
      end
    end
    endcase
  end
end
endmodule
