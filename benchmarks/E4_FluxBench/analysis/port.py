"""Bounded PicoRV32 synthesis-stage protocol port. No model or physical flow."""
import hashlib,json,os,pathlib,subprocess,time
ROOT=pathlib.Path(os.environ['E4_WORK_ROOT'])
ASSET=ROOT/'assets/fluxbench'; OUT=ROOT/'results/fluxbench/port-v1'
YOSYS=ROOT/'tools/verithoughts/yosys041-install/bin/yosys'
IV=ROOT/'tools/cvdp/iverilog-install/bin/iverilog'
VVP=IV.with_name('vvp')
OUT.mkdir(parents=True,exist_ok=True)
env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG','TMPDIR']}
env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
runs=[]
def run(name,args,expect=0):
    start=time.monotonic()
    try:
        p=subprocess.run([str(a) for a in args],cwd=OUT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
        text=p.stdout.decode(errors='replace'); code=p.returncode; timeout=False
    except subprocess.TimeoutExpired as e:
        text=(e.stdout or b'').decode(errors='replace'); code=None; timeout=True
    (OUT/(name+'.log')).write_text(text)
    rec=dict(id=name,command=[str(a) for a in args],exit_code=code,timeout=timeout,seconds=time.monotonic()-start,expected_exit=expect)
    runs.append(rec)
    if (expect==0 and code!=0) or (expect=='nonzero' and (code is None or code==0)):
        raise RuntimeError(rec)
    return text
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
    assert sha(ASSET/'picorv32.v')=='0836050971b3c6cdd28ac3b1e5719a67fb645161912bef1e472e63995ceb0622'
    (OUT/'constraints.json').write_text(json.dumps(dict(task='PICO_SYNTH_001',top='picorv32',parameters='upstream defaults',clock='clk',clock_period_ns=10,physical_checks='not_run',timing_constraint_applied=False,cycles=1000,reset_cycles=5),indent=2)+'\n')
    run('yosys-version',[YOSYS,'-V'])
    run('iverilog-version',[IV,'-V'])
    for name,flag in [('mapped',''),('alternative','-noabc')]:
        script=f'read_verilog {ASSET}/picorv32.v; synth -top picorv32 {flag}; check -assert; rename picorv32 impl; write_verilog {name}.v; write_json {name}.json'
        run('synth-'+name,[YOSYS,'-p',script])
        run('reload-'+name,[YOSYS,'-p',f'read_verilog {name}.v; hierarchy -check -top impl; proc; check -assert; stat'])
        design=json.loads((OUT/(name+'.json')).read_text())['modules']['impl']
        assert design['cells'] and set(['clk','resetn','mem_addr','mem_valid']).issubset(design['ports'])
    # Original and synthesized instances receive identical deterministic memory.
    tb='''module tb;
reg clk=0; always #5 clk=~clk;
reg resetn=0;
wire [31:0] a0,a1,d0,d1; wire [3:0] w0,w1; wire v0,v1,i0,i1,t0,t1;
reg [31:0] r0,r1;
always @* begin
case(a0) 0:r0=32'h00100093; 4:r0=32'h00108093; 8:r0=32'hffdff06f; default:r0=32'h00000013; endcase
case(a1) 0:r1=32'h00100093; 4:r1=32'h00108093; 8:r1=32'hffdff06f; default:r1=32'h00000013; endcase
end
picorv32 refcpu(.clk(clk),.resetn(resetn),.trap(t0),.mem_valid(v0),.mem_instr(i0),.mem_ready(1'b1),.mem_addr(a0),.mem_wdata(d0),.mem_wstrb(w0),.mem_rdata(r0),.pcpi_wr(1'b0),.pcpi_rd(32'b0),.pcpi_wait(1'b0),.pcpi_ready(1'b0),.irq(32'b0));
impl dut(.clk(clk),.resetn(resetn),.trap(t1),.mem_valid(v1),.mem_instr(i1),.mem_ready(1'b1),.mem_addr(a1),.mem_wdata(d1),.mem_wstrb(w1),.mem_rdata(r1),.pcpi_wr(1'b0),.pcpi_rd(32'b0),.pcpi_wait(1'b0),.pcpi_ready(1'b0),.irq(32'b0));
integer n; integer fetches=0;
initial begin
repeat(5) @(negedge clk); resetn=1;
for(n=0;n<1000;n=n+1) begin
@(negedge clk);
if ({t0,v0} !== {t1,v1}) $fatal(1,"control mismatch cycle %d",n);
if(v0===1'b1) begin
if ({i0,a0,w0} !== {i1,a1,w1}) $fatal(1,"bus mismatch cycle %d",n);
if(w0!=0 && d0!==d1) $fatal(1,"data mismatch");
if(i0) fetches=fetches+1;
end
end
if(fetches<10 || t0!==0) $fatal(1,"insufficient execution");
$display("VERIFIED cycles=1000 fetches=%0d",fetches); $finish;
end
endmodule
'''
    (OUT/'tb.v').write_text(tb)
    for name in ['mapped','alternative']:
        run('compile-'+name,[IV,'-g2012','-s','tb','-o',name+'.vvp','tb.v',ASSET/'picorv32.v',name+'.v'])
        text=run('simulate-'+name,[VVP,name+'.vvp'])
        assert 'VERIFIED cycles=1000 fetches=' in text
    # A concrete RTL mutation must be distinguished from a valid alternative.
    bad=(OUT/'mapped.v').read_text().replace('module impl(', 'module impl(')
    # Mutate the observed address in the testbench, not upstream reference RTL.
    (OUT/'tb-negative.v').write_text(tb.replace('{i1,a1,w1}',"{i1,32'b0,w1}"))
    run('compile-negative',[IV,'-g2012','-s','tb','-o','negative.vvp','tb-negative.v',ASSET/'picorv32.v','mapped.v'])
    run('simulate-negative',[VVP,'negative.vvp'],expect='nonzero')
    (OUT/'invalid.v').write_text('module invalid( this is not verilog')
    run('parse-negative',[YOSYS,'-p','read_verilog invalid.v'],expect='nonzero')
    status='reference_calibration'
finally:
    summary=dict(task='PICO_SYNTH_001',status=locals().get('status','resource_blocked'),port='synthesis_stage_only',model_calls=0,paid_cost_usd=0,thread_cap=4,command_timeout_seconds=120,runs=runs,
      tools={str(p):sha(p) for p in [YOSYS,IV,VVP]},
      artifacts={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.suffix in ['.v','.json'] and p.name!='summary.json'},
      excluded_stages=['physical_implementation','ECO','STA','GDS','clock_gating_validation'],functional_scope='1000-cycle single-program differential simulation; not formal equivalence')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
