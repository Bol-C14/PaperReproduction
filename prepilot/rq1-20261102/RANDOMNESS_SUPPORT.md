# Vivado randomness/repeatability support check — no new Vivado process

Evidence checked: the **actual installed Vivado 2025.1 build 6140274** help for `route_design` and `phys_opt_design`, captured in the existing no-edit log and extracted verbatim to source_audit/installed_vivado_2025_1_command_help.txt. Neither command's printed syntax/options contains a command-level random-seed option. The executed commands and local Tcl do not set a seed. This establishes **no verified supported explicit seed control for the selected commands in this experiment**. It does not prove that no undocumented/private parameter exists anywhere in Vivado; no such parameter was guessed, set or searched by launching the tool.

The captured 2025.1 route help explicitly says `-ultrathreads` trades runtime for repeatability. It was not used. `general.maxThreads=2` is supported and corroborated by runtime route/physopt messages; controlling thread count is a reproducibility control, not an RNG-seed control or guarantee of determinism. Avoiding ultrathreads does not prove all other sources of variation absent.

The current official online UG835 route_design page (2026.1, corroboration only, not substituted for the installed-version evidence) likewise exposes no seed option and documents the ultrathreads repeatability tradeoff:
https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/route_design

AMD answer record 61599 (https://adaptivesupport.amd.com/s/article/61599?language=en_US) was discovered as a repeatability source, but its full page rendered only a CSS/loading error in this session. The version-specific 2025.1 online route/physopt pages were inaccessible through the browsing tool. Do not infer their missing details from snippets or community claims. No absolute deterministic/reproducibility guarantee is attributed to that unread article.

Future reporting: use **fresh-process technical repetitions under fixed documented settings**, not “different-seed trials”. Record version, thread cap, exact input, scripts/flags and process order. Do not repurpose the validator's LFSR stimulus seed, an external selection RNG seed or a place/route directive as an implementation random seed. If a supported seed interface is later found in primary version-matched material, audit that exact interface and freeze a new protocol before using it.
