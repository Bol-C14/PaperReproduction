#!/usr/bin/env python3
"""Offline import validation only; never invokes a model or network service."""
import json
import math
from pathlib import Path
import sys

MODULE_FIELDS={'inputs','outputs','overall functionality','critical submodules','design choices','timing constraints'}
DESIGN_FIELDS={'design name','design functionality','primary inputs','primary outputs','key design characteristics',
               'key modules and functionalities','module interactions','design optimizations','potential applications','timing considerations'}


def summary_cache(cache, source_sha256):
    if cache['source_sha256']!=source_sha256: raise ValueError('Summary belongs to different source bytes')
    if not cache.get('modules'): raise ValueError('Missing module summaries')
    for module in cache['modules']:
        if set(module['summary'])!=MODULE_FIELDS: raise ValueError('Incomplete module summary fields')
    if set(cache['design_summary'])!=DESIGN_FIELDS: raise ValueError('Incomplete circuit summary fields')
    embedding=cache['embedding']
    if len(embedding)!=384 or any(type(v) not in (int,float) or not math.isfinite(v) for v in embedding):
        raise ValueError('Expected finite 384-dimensional all-MiniLM-L6-v2 embedding')
    if sum(v*v for v in embedding)==0: raise ValueError('Zero embedding')
    for field in ['summary_model','summary_model_revision','embedding_model','embedding_model_revision',
                  'prompt_sha256','embedding_normalization','embedding_truncation','generation_provenance']:
        if not cache.get(field): raise ValueError('Missing model provenance '+field)
    return embedding


def proposal(response, context):
    # Legal free-tool options only. This cannot validate unreleased industrial options.
    chosen=response['configuration']
    if set(chosen)!={'mode','noalumacc'} or type(chosen['noalumacc']) is not bool:
        raise ValueError('Expected exact legal configuration parameter dictionary')
    match=[c for c in context['legal_configs'] if c['mode']==chosen['mode'] and c['noalumacc']==chosen['noalumacc']]
    if len(match)!=1: raise ValueError('Configuration outside frozen legal pool')
    if match[0]['id'] in {h['config'] for h in context['target_history']}:
        raise ValueError('Duplicate trial would consume the same bounded budget')
    return match[0]['id']


if __name__=='__main__':
    if len(sys.argv)!=4 or sys.argv[1] not in ('summary','proposal'):
        raise SystemExit('summary CACHE_JSON SOURCE_SHA256 | proposal RESPONSE_JSON CONTEXT_ARTIFACT_JSON')
    data=json.loads(Path(sys.argv[2]).read_text())
    if sys.argv[1]=='summary':
        summary_cache(data,sys.argv[3]);print('Offline summary cache accepted; no model execution performed.')
    else:
        context=json.loads(Path(sys.argv[3]).read_text())['request']
        print(proposal(data,context))
