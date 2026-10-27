`timescale 1ns/1ps
 module top #(parameter ARST_LVL = 1'b0,      // asynchronous reset level
                 parameter INIT_ENA = 1'b1,      // COP Enabled after reset
                 parameter SERV_WD_0 = 16'h5555, // First Service Word
		 parameter SERV_WD_1 = 16'haaaa, // Second Service Word
                 parameter COUNT_SIZE = 16,      // Main counter size
                 parameter SINGLE_CYCLE = 1'b0,  // No bus wait state added
		 parameter DWIDTH = 16)          // Data bus width
  (
  // Wishbone Signals
  output [DWIDTH-1:0] wb_dat_o,     // databus output
  output              wb_ack_o,     // bus cycle acknowledge output
  input               wb_clk_i,     // master clock input
  input               wb_rst_i,     // synchronous active high reset
  input               arst_i,       // asynchronous reset
  input         [2:0] wb_adr_i,     // lower address bits
  input  [DWIDTH-1:0] wb_dat_i,     // databus input
  input               wb_we_i,      // write enable input
  input               wb_stb_i,     // stobe/core select signal
  input               wb_cyc_i,     // valid bus cycle input
  input         [1:0] wb_sel_i,     // Select byte in word bus transaction
  // COP IO Signals
  output              cop_rst_o,    // COP reset output, active low
  output              cop_irq_o,    // COP interrupt request signal output
  input               por_reset_i,  // System Power On Reset, active low
  input               startup_osc_i,// System Startup Oscillator
  input               stop_mode_i,  // System STOP Mode
  input               wait_mode_i,  // System WAIT Mode
  input               debug_mode_i, // System DEBUG Mode
  input               scantestmode  // Chip in in scan test mode
  );
  
  logic                  cop_event;     // COP status bit
  logic                  cop_flag;      // COP Rollover Flag
  logic            [1:0] cop_irq_en;    // COP Interrupt request enable
  logic [COUNT_SIZE-1:0] cop_counter;   // COP Counter Value
  logic [COUNT_SIZE-1:0] cop_capture;   // Counter value syncronized to bus_clk domain
  logic                  async_rst_b;   // Asyncronous reset
  logic                  sync_reset;    // Syncronous reset
  logic           [ 4:0] write_regs;    // Control register write strobes
  logic                  prescale_out;  //
  logic                  stop_ena;      // Clear COP Rollover Status Bit
  logic                  debug_ena;     // COP in Slave Mode, ext_sync_i selected
  logic                  wait_ena;      // Enable COP in system wait mode
  logic                  cop_ena;       // Enable COP Timout Counter
  logic                  cwp;           // COP write protect
  logic                  clck;          // COP lock
  logic                  reload_count;  // COP System service complete
  logic                  clear_event;   // Reset COP Event register
  logic [COUNT_SIZE-1:0] timeout_value; // Prescaler modulo
  logic                  counter_sync;  // 
  
  // Wishbone Bus interface
  cop_wb_bus #(.ARST_LVL(ARST_LVL),
               .SINGLE_CYCLE(SINGLE_CYCLE),
               .DWIDTH(DWIDTH))
    wishbone(
    .*,
    .irq_source   ( cnt_flag_o ),
    .read_regs    (               // in  -- read register bits
		   { cop_capture,
		     timeout_value,
		     {7'b0, cop_event, cop_irq_en, debug_ena, stop_ena, wait_ena,
		      cop_ena, cwp, clck}
		   }
		  )
  );

// -----------------------------------------------------------------------------
  cop_regs #(.ARST_LVL(ARST_LVL),
             .INIT_ENA(INIT_ENA),
             .SERV_WD_0(SERV_WD_0),
	     .SERV_WD_1(SERV_WD_1),
             .COUNT_SIZE(COUNT_SIZE),
             .DWIDTH(DWIDTH))
    regs(
    .*,
    .bus_clk        ( wb_clk_i ),
    .write_bus      ( wb_dat_i ) 
  );

// -----------------------------------------------------------------------------
  cop_count #(.COUNT_SIZE(COUNT_SIZE))
    counter(
    .*,
    .bus_clk           ( wb_clk_i )
  );

endmodule // cop_top


module cop_wb_bus #(parameter ARST_LVL = 1'b0,    // asynchronous reset level
  		    parameter DWIDTH = 16,
                    parameter SINGLE_CYCLE = 1'b0)
  (
  // Wishbone Signals
  output      [DWIDTH-1:0] wb_dat_o,     // databus output
  output                   wb_ack_o,     // bus cycle acknowledge output
  input                    wb_clk_i,     // master clock input
  input                    wb_rst_i,     // synchronous active high reset
  input                    arst_i,       // asynchronous reset
  input             [ 2:0] wb_adr_i,     // lower address bits
  input       [DWIDTH-1:0] wb_dat_i,     // databus input
  input                    wb_we_i,      // write enable input
  input                    wb_stb_i,     // stobe/core select signal
  input                    wb_cyc_i,     // valid bus cycle input
  input              [1:0] wb_sel_i,     // Select byte in word bus transaction
  // COP Control Signals
  output logic      [ 4:0] write_regs,   // Decode write control register
  output                   async_rst_b,  //
  output                   sync_reset,   //
  input                    irq_source,   //
  input             [47:0] read_regs     // status register bits
  );


  // registers
  logic                bus_wait_state;  // Holdoff wb_ack_o for one clock to add wait state
  logic  [DWIDTH-1:0]  rd_data_mux;     // Pseudo Register, WISHBONE Read Data Mux
  logic  [DWIDTH-1:0]  rd_data_reg;     // Latch for WISHBONE Read Data

  // Wires
  logic  eight_bit_bus;
  logic  module_sel;      // This module is selected for bus transaction
  logic  wb_wacc;         // WISHBONE Write Strobe (Clock gating signal)
  logic  wb_racc;         // WISHBONE Read Access (Clock gating signal)

  //
  // module body
  //

  // generate internal resets
  assign eight_bit_bus = (DWIDTH == 8);

  assign async_rst_b = arst_i ^ ARST_LVL;
  assign sync_reset = wb_rst_i;

  // generate wishbone signals
  assign module_sel = wb_cyc_i && wb_stb_i;
  assign wb_wacc    = module_sel && wb_we_i && (wb_ack_o || SINGLE_CYCLE);
  assign wb_racc    = module_sel && !wb_we_i;
  assign wb_ack_o   = SINGLE_CYCLE ? module_sel : ( module_sel && bus_wait_state);
  assign wb_dat_o   = SINGLE_CYCLE ? rd_data_mux : rd_data_reg;

  // generate acknowledge output signal, By using register all accesses takes two cycles.
  //  Accesses in back to back clock cycles are not possable.
  always_ff @(posedge wb_clk_i or negedge async_rst_b)
    if (!async_rst_b)
      bus_wait_state <=  1'b0;
    else if (sync_reset)
      bus_wait_state <=  1'b0;
    else
      bus_wait_state <=  module_sel && !bus_wait_state;

  // assign data read bus -- DAT_O
  always_ff @(posedge wb_clk_i)
    if ( wb_racc )                     // Clock gate for power saving
      rd_data_reg <= rd_data_mux;

      
  // WISHBONE Read Data Mux
  always_comb
      case ({eight_bit_bus, wb_adr_i}) // synopsys parallel_case
	// 8 bit Bus, 8 bit Granularity
	4'b1_000: rd_data_mux = read_regs[ 7: 0];  // 8 bit read address 0
	4'b1_001: rd_data_mux = read_regs[15: 8];  // 8 bit read address 1
	4'b1_010: rd_data_mux = read_regs[23:16];  // 8 bit read address 2
	4'b1_011: rd_data_mux = read_regs[31:24];  // 8 bit read address 3
	4'b1_100: rd_data_mux = read_regs[39:32];  // 8 bit read address 4
	4'b1_101: rd_data_mux = read_regs[47:40];  // 8 bit read address 5
	// 16 bit Bus, 16 bit Granularity
	4'b0_000: rd_data_mux = read_regs[15: 0];  // 16 bit read access address 0
	4'b0_001: rd_data_mux = read_regs[31:16];
	4'b0_010: rd_data_mux = read_regs[47:32];
      endcase

  // generate wishbone write register strobes -- one hot if 8 bit bus
  //                                             two hot if 16 bit bus
  always_comb
    begin
      write_regs = 0;
      if (wb_wacc)
	case ({eight_bit_bus, wb_adr_i}) // synopsys parallel_case
           // 8 bit Bus, 8 bit Granularity
	   5'b1_000 : write_regs = 5'b00001;
	   5'b1_001 : write_regs = 5'b00010;
	   5'b1_010 : write_regs = 5'b00100;
	   5'b1_011 : write_regs = 5'b01000;
	   5'b1_100 : write_regs = 5'b10000;
           // 16 bit Bus, 16 bit Granularity
	   5'b0_000 : write_regs = 5'b00011;
	   5'b0_001 : write_regs = 5'b01100;
	   5'b0_010 : write_regs = 5'b10000;
	   default: ;
	endcase
    end

endmodule  // cop_wb_bus


module cop_regs #(parameter ARST_LVL = 1'b0,      // asynchronous reset level
                  parameter INIT_ENA = 1'b1,      // COP Enabled after reset
                  parameter SERV_WD_0 = 16'h5555, // First Service Word
		  parameter SERV_WD_1 = 16'haaaa, // Second Service Word
                  parameter COUNT_SIZE = 16,
                  parameter DWIDTH = 16)
  (
  output logic [COUNT_SIZE-1:0] timeout_value,// COP timout Value
  output logic           [ 1:0] cop_irq_en,   // COP IRQ Enable/Value
  output logic                  debug_ena,    // Enable COP in system debug mode
  output logic                  stop_ena,     // Enable COP in system stop mode
  output logic                  wait_ena,     // Enable COP in system wait mode
  output logic                  cop_ena,      // Enable COP Timout Counter
  output logic                  cwp,          // COP write protect
  output logic                  clck,         // COP lock
  output logic                  reload_count, // COP System service complete
  output logic                  clear_event,  // Reset the COP event register
  input                       bus_clk,      // Control register bus clock
  input                       async_rst_b,  // Async reset signal
  input                       sync_reset,   // Syncronous reset signal
  input                       cop_flag,     // COP Rollover Flag
  input          [DWIDTH-1:0] write_bus,    // Write Data Bus
  input                [ 4:0] write_regs    // Write Register strobes
  );


  // registers
  logic        service_cop; // Service register to reload COP Timeout Counter

  // Wires
  logic [15:0] write_data;  // Data bus mux for 8 or 16 bit module bus

  //
  // module body
  //
  
  assign write_data = (DWIDTH == 8) ? {write_bus[7:0], write_bus[7:0]} : write_bus;
  
  
  // generate wishbone write registers
  always_ff @(posedge bus_clk or negedge async_rst_b)
    if (!async_rst_b)
      begin
	timeout_value <= {COUNT_SIZE{1'b1}};
        cop_irq_en    <= 2'b00;
        debug_ena     <= 1'b0;
        stop_ena      <= 1'b0;
        wait_ena      <= 1'b0;
        cop_ena       <= INIT_ENA;
        cwp           <= 1'b0;
	clck          <= 1'b0;
	reload_count  <= 1'b0;
	service_cop   <= 0;
       end
    else if (sync_reset)
      begin
	timeout_value <= {COUNT_SIZE{1'b1}};
        cop_irq_en    <= 2'b00;
        debug_ena     <= 1'b0;
        stop_ena      <= 1'b0;
        wait_ena      <= 1'b0;
        cop_ena       <= INIT_ENA;
        cwp           <= 1'b0;
	clck          <= 1'b0;
	reload_count  <= 1'b0;
	service_cop   <= 0;
      end
    else
      case (write_regs) // synopsys parallel_case
         5'b00011 :  // Word Write
           begin
             clear_event <= write_data[8];
             cop_irq_en  <= write_data[7:6];
             debug_ena   <= (!cop_ena || !write_data[2]) ? write_data[5] : debug_ena;
             stop_ena    <= (!cop_ena || !write_data[2]) ? write_data[4] : stop_ena;
             wait_ena    <= (!cop_ena || !write_data[2]) ? write_data[3] : wait_ena;
             cop_ena     <= cwp  ? cop_ena : write_data[2];
             cwp         <= clck ? cwp : write_data[1];
             clck        <= clck || write_data[0];
           end
         5'b00001 :  // Low Byte Write
           begin
             cop_irq_en  <= write_data[7:6];
             debug_ena   <= (!cop_ena || !write_data[2]) ? write_data[5] : debug_ena;
             stop_ena    <= (!cop_ena || !write_data[2]) ? write_data[4] : stop_ena;
             wait_ena    <= (!cop_ena || !write_data[2]) ? write_data[3] : wait_ena;
             cop_ena     <= cwp ? cop_ena : write_data[2];
             cwp         <= clck ? cwp : write_data[1];
             clck        <= clck || write_data[0];
           end
         5'b00010 :  // High Byte Write
           begin
             clear_event  <= write_data[0];
           end

	 5'b01100 : timeout_value        <= cop_ena ? timeout_value : write_data;
         5'b00100 : timeout_value[ 7:0]  <= cop_ena ? timeout_value[ 7:0] : write_data[7:0];
         5'b01000 : timeout_value[15:8]  <= cop_ena ? timeout_value[15:8] : write_data[7:0];
	 
         5'b10000 :
	   begin
	     service_cop  <= (write_data == SERV_WD_0);
	     reload_count <= service_cop && (write_data == SERV_WD_1);
	   end
         default:
	   begin
	     reload_count <= 1'b0;
	     clear_event  <= 1'b0;
	   end
      endcase


endmodule  // cop_regs


module cop_count #(parameter COUNT_SIZE = 16)
  (
  output logic [COUNT_SIZE-1:0] cop_counter,   // Modulo Counter value
  output logic [COUNT_SIZE-1:0] cop_capture,   // Counter value syncronized to bus_clk domain
  output logic                  cop_rst_o,     // COP Reset
  output logic                  cop_irq_o,     // COP Interrupt Request
  output logic                  cop_event,     // COP status bit
  input                         async_rst_b,   // Asyncronous reset signal
  input                         sync_reset,    // Syncronous reset signal
  input                         por_reset_i,   // System Power On Reset, active low
  input                         startup_osc_i, // System Startup Oscillator
  input                         bus_clk,       // Control register bus clock
  input                         reload_count,  // Correct control words written
  input                         clear_event,   // Reset the COP event register
  input                         debug_mode_i,  // System DEBUG Mode
  input                         debug_ena,     // Enable COP in system debug mode
  input                         wait_ena,      // Enable COP in system wait mode
  input                         wait_mode_i,   // System WAIT Mode
  input                         stop_ena,      // Enable COP in system stop mode
  input                         stop_mode_i,   // System STOP Mode
  input                         cop_ena,       // Enable COP Timout Counter
  input                  [ 1:0] cop_irq_en,    // COP IRQ Enable/Value
  input        [COUNT_SIZE-1:0] timeout_value, // COP Counter initial value
  input                         scantestmode   // Chip in in scan test mode
  );


  logic  stop_counter;    // Enable COP because of external inputs
  logic  cop_clk;         // Clock for COP Timeout counter
  logic  event_reset;     // Clear COP event status bit
  logic  cop_clk_posedge; // Syncronizing signal to move data to bus_clk domain

  logic  cop_irq_dec;     // COP Interrupt Request Decode
  logic  cop_irq;         // COP Interrupt Request
  logic  reload_1;        // Resync register for commands crossing from bus_clk domain to cop_clk domain
  logic  reload_2;        //
  logic  cop_clk_resync1; //
  logic  cop_clk_resync2; //

  
  assign event_reset = reload_count || clear_event;

  assign stop_counter = (debug_mode_i && debug_ena) ||
		        (wait_mode_i && wait_ena) || (stop_mode_i && stop_ena);

  assign cop_clk = scantestmode ? bus_clk : startup_osc_i;

  
  assign cop_clk_posedge = cop_clk_resync1 && !cop_clk_resync2;

  //  Watchdog Timout Counter
  always_ff @(posedge cop_clk or negedge async_rst_b)
    if ( !async_rst_b )
      cop_counter  <= '1;
    else if ( reload_2 )
      cop_counter  <= timeout_value;
    else if ( !stop_counter )
      cop_counter  <= --cop_counter;

  //  COP Output Register
  always_ff @(posedge cop_clk or negedge por_reset_i)
    if ( !por_reset_i )
      cop_rst_o <= '0;
    else if ( reload_2 )
      cop_rst_o <= '0;
    else
      cop_rst_o <= (cop_counter == '0);

  // Clock domain crossing registers. Take data from cop_clk domain and move it
  //  to the bus_clk domain.
  always_ff @(posedge bus_clk or negedge async_rst_b)
    if ( !async_rst_b )
      begin
        cop_clk_resync1 <= '0;
        cop_clk_resync2 <= '0;
	cop_capture     <= '1;
      end
    else if (sync_reset)
      begin
        cop_clk_resync1 <= '0;
        cop_clk_resync2 <= '0;
	cop_capture     <= '1;
      end
    else
      begin
        cop_clk_resync1 <= cop_clk;
        cop_clk_resync2 <= cop_clk_resync1;
	cop_capture     <= cop_clk_posedge ? cop_counter : cop_capture;
      end

  // Stage one of pulse strecher and resync
  always_ff @(posedge bus_clk or negedge async_rst_b)
    if ( !async_rst_b )
      reload_1 <= '0;
    else if (sync_reset)
      reload_1 <= '0;
    else
      reload_1 <= (sync_reset || reload_count || !cop_ena) || (reload_1 && !reload_2);

  // Stage two pulse strecher and resync
  always_ff @(posedge cop_clk or negedge por_reset_i)
    if ( !por_reset_i )
      reload_2 <= '1;
    else
      reload_2 <= reload_1;

  // Decode COP Interrupt Request
  always_comb
    case (cop_irq_en) // synopsys parallel_case
       2'b01 : cop_irq_dec = (cop_counter <= 16);
       2'b10 : cop_irq_dec = (cop_counter <= 32);
       2'b11 : cop_irq_dec = (cop_counter <= 64);
       default: cop_irq_dec = '0;
    endcase

  //  Watchdog Interrupt and resync
  always_ff @(posedge bus_clk or negedge async_rst_b)
    if ( !async_rst_b )
      begin
        cop_irq   <= '0;
        cop_irq_o <= '0;
      end
    else if (sync_reset)
      begin
        cop_irq   <= '0;
        cop_irq_o <= '0;
      end
    else
      begin
        cop_irq   <= cop_irq_dec;
        cop_irq_o <= cop_irq;
      end

  //  Watchdog Status Bit
  always_ff @(posedge bus_clk or negedge por_reset_i)
    if ( !por_reset_i )
      cop_event <= '0;
    else
      cop_event <= cop_rst_o || (cop_event && !event_reset);

endmodule  // cop_count


