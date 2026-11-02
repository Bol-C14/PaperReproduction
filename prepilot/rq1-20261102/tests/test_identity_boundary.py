"""Synthetic boundary tests only; never invokes EDA or claims circuit evidence."""
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from identity_v2 import canonical_file
HDL='''// Tool Version: synthetic fixture, not a tool run
// Date        : first
// Command     : write_verilog -force -mode funcsim snapshot_funcsim.v
`timescale 1 ps / 1 ps
module demo(input a, output y);
wire internal;
LUT2 #(.INIT(4'h8)) gate(.I0(a), .I1(a), .O(y));
endmodule
'''
XDC='# Command Used: write_xdc -force snapshot_constraints.xdc\ncreate_clock -period 1.570 [get_ports clk]\n'
class IdentityBoundary(unittest.TestCase):
 def compare(self,a,b,suffix='.v'):
  with tempfile.TemporaryDirectory() as d:
   x=Path(d)/('a'+suffix);y=Path(d)/('b'+suffix);x.write_text(a);y.write_text(b)
   return canonical_file(x)==canonical_file(y)
 def test_date_only(self):self.assertTrue(self.compare(HDL,HDL.replace(': first',': second')))
 def test_timescale(self):self.assertFalse(self.compare(HDL,HDL.replace('1 ps / 1 ps','1 ns / 1 ps')))
 def test_lut_init(self):self.assertFalse(self.compare(HDL,HDL.replace("4'h8","4'h9")))
 def test_body_comment(self):self.assertFalse(self.compare(HDL,HDL.replace('wire internal;','// synthesis translate_off\nwire internal;')))
 def test_body_directive(self):self.assertFalse(self.compare(HDL,HDL.replace('wire internal;','`define ALTERED 1\nwire internal;')))
 def test_wire(self):self.assertFalse(self.compare(HDL,HDL.replace('wire internal;','wire changed;')))
 def test_preamble_directive_rejected(self):
  with self.assertRaises(ValueError):self.compare(HDL,HDL.replace('`timescale','`define ALTERED 1\n`timescale'))
 def test_wrapped_command_rejected(self):
  with self.assertRaises(ValueError):self.compare(HDL,HDL.replace('funcsim snapshot_funcsim.v','funcsim\n//               snapshot_funcsim.v'))
 def test_xdc_identical(self):self.assertTrue(self.compare(XDC,XDC,'.xdc'))
 def test_xdc_period(self):self.assertFalse(self.compare(XDC,XDC.replace('1.570','1.580'),'.xdc'))
 def test_xdc_comment(self):self.assertFalse(self.compare(XDC,XDC+'# extra\n','.xdc'))
if __name__=='__main__':unittest.main()
