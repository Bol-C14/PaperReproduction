# Supplemental logging repair, after frozen attempt1

The first complete eight-control experiment finished 2026-10-28T10:46:57.683212Z. All predictions matched and original/port labels agreed on all controls. No fixture, original evaluator, port implementation or original result is changed.

Inspection of the direct Yosys port's 160-step failure stdout found it ends mid-line at SAT frame 160. Yosys's fatal `-verify` exit did not flush its buffered stdout pipe. The retained stderr explicitly reports proof failure, and Icarus independently retains the first divergence at rising edge 60, but the complete SAT witness should be preserved.

Authorize within this amendment exactly **one supplemental invocation** of the already emitted and frozen-assumption 160-step script, adding only `stdbuf -o0` as in the original evaluator's tool invocation. This changes logging buffering only: same Yosys image/binary, RTL files, script, bound, initialization, 150-second timeout and resource/isolation caps. No horizon tuning, altered assumptions, fixture changes or re-evaluation of the eight cases. This is a logging repair, not an additional original result or an independent statistical replicate.

The supplemental source mount is read-only. Record script/input SHA256 values, timestamp, exit code, full streams, wall/resource measurements and the returned witness's first asserted trigger frame; do not claim that frame is the globally shortest witness. Commit this amendment before running it. Retain the incomplete first log without overwriting it.
