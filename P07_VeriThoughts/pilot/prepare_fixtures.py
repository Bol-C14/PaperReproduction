"""Author-created synthetic controls; preparation only, no HDL execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
cases = []

def add(name, gold, candidate, kind, truth, official, **meta):
    item = dict(id=name, kind=kind, independent_truth=truth,
                predicted_official=official, **meta)
    directory = ROOT / 'fixtures' / name
    directory.mkdir(parents=True, exist_ok=True)
    for filename, text in [('gold.v', gold), ('candidate.v', candidate)]:
        (directory / filename).write_text(text + '\n')
        item[filename + '_sha256'] = hashlib.sha256((text + '\n').encode()).hexdigest()
    cases.append(item)

add('comb_demorgan',
    'module top(input a,b, output y); assign y=~(a&b); endmodule',
    'module top(input a,b, output y); assign y=(~a)|(~b); endmodule',
    'comb', 'equivalent', 'pass', model='nand')
add('comb_mismatch',
    'module top(input a,b, output y); assign y=a&b; endmodule',
    'module top(input a,b, output y); assign y=a|b; endmodule',
    'comb', 'non_equivalent', 'fail', model='and_or')
add('seq_modular',
    "module top(input clk, output reg [3:0] q); always @(posedge clk) q<=q+4'd1; endmodule",
    "module top(input clk, output reg [3:0] q); always @(posedge clk) q<=q-4'd15; endmodule",
    'seq', 'equivalent_under_zero_init', 'pass', width=4, model='increment_subtract')
add('seq_increment',
    "module top(input clk, output reg [3:0] q); always @(posedge clk) q<=q+4'd1; endmodule",
    "module top(input clk, output reg [3:0] q); always @(posedge clk) q<=q+4'd2; endmodule",
    'seq', 'non_equivalent', 'fail', width=4, model='increment_two')
add('delayed_pulse',
    "module top(input clk, output y); reg [7:0] count; always @(posedge clk) count<=count+8'd1; assign y=(count==8'd60); endmodule",
    "module top(input clk, output y); reg [7:0] count; always @(posedge clk) count<=count+8'd1; assign y=1'b0; endmodule",
    'seq', 'non_equivalent', 'pass', width=8, model='delayed', first_bad_rising_edge=60)
add('empty_discovery',
    "module top; wire unused; assign unused=1'b0; endmodule",
    'THIS IS NOT LEGAL VERILOG',
    'invalid', 'invalid_candidate', 'pass', model='empty_module_discovery')
add('helper_inline',
    'module helper(input a,b, output y); assign y=a^b; endmodule\nmodule top(input a,b, output y); helper h(a,b,y); endmodule',
    'module top(input a,b, output y); assign y=(a&~b)|(~a&b); endmodule',
    'comb', 'equivalent_at_top_interface', 'fail', model='xor')
add('syntax_error',
    'module top(input a,b, output y); assign y=a&b; endmodule',
    'module top(input a,b, output y); assign y=; endmodule',
    'invalid', 'invalid_candidate', 'fail', model='invalid_expression')

(ROOT / 'fixtures.json').write_text(json.dumps(cases, indent=2) + '\n')
source = (ROOT.parent / 'evidence/evaluation_verithoughts/evaluation_script.py.txt').read_bytes()
# Audit snapshot adds one newline to the exact upstream file. Verify Git blob identity.
original = source[:-1]
blob = hashlib.sha1(b'blob ' + str(len(original)).encode() + b'\0' + original).hexdigest()
assert blob == '74963ae51ca6360b5b5944b03c266f7f48309b06', blob
(ROOT / 'upstream').mkdir(exist_ok=True)
(ROOT / 'upstream/evaluation_script.py').write_bytes(original)
(ROOT / 'upstream/provenance.json').write_text(json.dumps(dict(
    repository='https://github.com/wilyub/VeriThoughts',
    commit='f44c2af999de62bd27e90e73ce9cbd4f97fbe55c',
    path='evaluation_verithoughts/evaluation_script.py', git_blob_sha1=blob,
    sha256=hashlib.sha256(original).hexdigest(), modified=False), indent=2) + '\n')
print('Prepared', len(cases), 'fixtures; verified upstream blob', blob)
