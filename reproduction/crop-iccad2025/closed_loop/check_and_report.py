#!/usr/bin/env python3
"""Independent result accounting and trace checks; does not run synthesis."""
import collections
import csv
import json
from pathlib import Path
import statistics
import study

ROOT=Path(__file__).resolve().parent


def main():
    manifest=json.loads((ROOT/'manifest.json').read_text())
    rows=json.loads((ROOT/'results.json').read_text())
    assert len(rows)==272 and all(r['status']=='ok' for r in rows)
    assert collections.Counter(r['phase'] for r in rows)=={'history':48,'online':192,'posthoc_oracle':32}
    byinv={r['invocation']:r for r in rows}
    online=[r for r in rows if r['phase']=='online']
    last_online=max(r['invocation'] for r in online)
    assert min(r['invocation'] for r in rows if r['phase']=='posthoc_oracle')>last_online
    known_metrics={};feature_vectors={}
    for row in rows:
        folder=ROOT/row['folder']
        assert row['objective']==row['lut_count']*row['lut_depth']
        assert 'Networks are equivalent.' in (folder/'cec.log').read_text()
        key=(row['design'],row['config']);pair=(row['lut_count'],row['lut_depth'])
        assert key not in known_metrics or known_metrics[key]==pair
        known_metrics[key]=pair
        vec=study.structural_features(json.loads((folder/'highlevel.json').read_text())['modules']['dut'])
        assert row['design'] not in feature_vectors or feature_vectors[row['design']]==vec
        feature_vectors[row['design']]=vec
    traces=[]; feedback_decision_changes=0; feedback_comparisons=0; feedback_score_changes=0
    targets=[d['id'] for d in manifest['designs'] if d['role']=='target']
    prior_families={d['family'] for d in manifest['designs'] if d['role']=='prior'}
    assert not prior_families.intersection(d['family'] for d in manifest['designs'] if d['role']=='target')
    for design in targets:
        oracle=min(r['objective'] for r in rows if r['phase']=='posthoc_oracle' and r['design']==design)
        for seed in manifest['seeds']:
            for arm in manifest['arms']:
                trace=sorted([r for r in online if (r['design'],r['seed'],r['arm'])==(design,seed,arm)],key=lambda r:r['iteration'])
                assert len(trace)==4 and len({r['config'] for r in trace})==4
                assert trace[0]['config']=='c0'
                expected=[]
                for row in trace:
                    artifact=json.loads((ROOT/row['context']).read_text())
                    request=artifact['request']
                    assert request['target_history']==expected
                    assert request['target_history_hash']==study.digest(expected)
                    assert artifact['response']==study.propose(request)
                    assert artifact['response']['config']==row['config']
                    if row['iteration']>=2 and arm!='random_search':
                        # Keep the same visited configurations; remove only their
                        # measured performance differences. No new oracle calls.
                        flat=json.loads(json.dumps(request))
                        for history_row in flat['target_history']:
                            history_row['objective']=flat['target_history'][0]['objective']
                        counterfactual=study.propose(flat)
                        feedback_comparisons+=1
                        feedback_decision_changes+=int(counterfactual['config']!=row['config'])
                        feedback_score_changes+=int(counterfactual['candidate_scores']!=artifact['response']['candidate_scores'])
                    expected.append(dict(config=row['config'],objective=row['objective'],status=row['status'],invocation=row['invocation']))
                archive=json.loads((ROOT/'archives'/f'{design}_{seed}_{arm}.json').read_text())
                assert archive['target_history']==expected and archive['target_history_hash']==study.digest(expected)
                best=min(trace,key=lambda r:r['objective'])
                traces.append(dict(design=design,seed=seed,arm=arm,retrieved=trace[0]['retrieved'],
                                   configurations=','.join(r['config'] for r in trace),
                                   best_config=best['config'],best_lut_count=best['lut_count'],best_lut_depth=best['lut_depth'],
                                   best_objective=best['objective'],common_initial_objective=trace[0]['objective'],
                                   oracle_objective=oracle,normalized_to_initial=best['objective']/trace[0]['objective'],
                                   ratio_to_oracle=best['objective']/oracle,oracle_hit=best['objective']==oracle))
    with (ROOT/'trace_summary.csv').open('w') as out:
        writer=csv.DictWriter(out,fieldnames=list(traces[0]));writer.writeheader();writer.writerows(traces)
    arms={}
    for arm in manifest['arms']:
        subset=[r for r in traces if r['arm']==arm]
        arms[arm]=dict(mean_best_over_initial=statistics.mean(r['normalized_to_initial'] for r in subset),
                       mean_best_over_oracle=statistics.mean(r['ratio_to_oracle'] for r in subset),
                       oracle_hits=sum(r['oracle_hit'] for r in subset),target_seed_cases=len(subset))
    pairs={}
    for other in ['random_retrieval','no_retrieval','random_search']:
        outcomes=collections.Counter()
        for design in targets:
            for seed in manifest['seeds']:
                a=next(r for r in traces if (r['design'],r['seed'],r['arm'])==(design,seed,'structural'))
                b=next(r for r in traces if (r['design'],r['seed'],r['arm'])==(design,seed,other))
                outcomes['win' if a['best_objective']<b['best_objective'] else 'loss' if a['best_objective']>b['best_objective'] else 'tie']+=1
        pairs[other]=dict(outcomes)
    # Prove the independent checker notices an incorrect result, using a deliberately
    # corrupted COPY. The delivered original mapped netlist is unchanged.
    example=next(r for r in rows if r['phase']=='posthoc_oracle' and r['design']=='fir3')
    bad=json.loads((ROOT/example['folder']/'mapped.json').read_text())
    bad['modules']['dut']['ports']['y']['bits'][0]='1'
    mutation=ROOT/'checks'/'deliberately_invalid_output.json';study.dump(mutation,bad)
    detected=False
    try:
        study.verify_luts(mutation,next(d for d in manifest['designs'] if d['id']=='fir3'))
    except ValueError as exc:
        detected=True;mutation_error=str(exc)
    assert detected
    study.dump(ROOT/'analysis.json',dict(arms=arms,structural_paired_outcomes=pairs,
        measurement_calls=272,abc_equivalence_proofs=272,independent_reference_vector_checks=272*256,
        unique_design_configuration_pairs=len(known_metrics),feedback_counterfactual_comparisons=feedback_comparisons,
        feedback_counterfactual_changed_decisions=feedback_decision_changes,feedback_counterfactual_changed_scores=feedback_score_changes,
        mutation_control=dict(status='invalid mapped output correctly rejected',error=mutation_error),
        checks=['exact matched online budgets','no repeated config within trace','common initialization',
                'per-query archives isolated','proposal replay identical','no oracle information in search',
                'identical repeated measurement metrics','stable pre-synthesis structural features',
                'formal CEC success logs','reported objective equals raw metric product'],
        phase_seconds={phase:sum(r['elapsed_seconds'] for r in rows if r['phase']==phase)
                       for phase in ['history','online','posthoc_oracle']}))
    print(json.dumps(json.loads((ROOT/'analysis.json').read_text()),indent=2))


if __name__=='__main__': main()
