# Log provenance

`session-observations.txt` is a clearly labeled transcription of the initial tool observations, not a fabricated direct shell capture. Other named stdout/stderr/build/install logs were redirected directly during their actions. The initial zero-count preflight preceded later work and is historical.

Failed stages remain: APT snapshot403, build-pending smoke without engine, ANSI-Verilog smoke with actual engine returning nonfinite values. The latter is not counted as a successful case. Current non-ANSI successful STA inputs/logs are separate. The default all-target build was deliberately superseded by targeted `ot-shell` compilation.

The first plot invocation warned about the read-only default cache; final plotting used writable `MPLCONFIGDIR`. Figures and metric summaries are derived, not original-paper plots.

Verification includes51 raw-output metric/tree checks and394 exact upstream source-file hashes. The minimal source archive independently extracted/configured successfully. No full upstream regression suite, independent STA cross-calibration, physical verification or model training is implied.
