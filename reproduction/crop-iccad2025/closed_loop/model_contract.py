#!/usr/bin/env python3
"""Offline import validation only; never invokes a model or network service."""
import json
import math
from pathlib import Path
import sys

MODULE_FIELDS={'inputs','outputs','overall functionality','critical submodules','design choices','timing constraints'}
DESIGN_FIELDS={'design name','design functionality','primary inputs','primary outputs','key design characteristics',
               'key modules and functionalities','module interactions','design optimizations','potential applications','timing considerations'}


def summary_fields(summary, required):
    if not isinstance(summary, dict) or set(summary) != required:
        raise ValueError('Expected exact summary field dictionary')
    if any(not isinstance(v, str) or not v.strip() or len(v) > 256 for v in summary.values()):
        raise ValueError('Summary values must be nonempty strings of at most 256 characters')
    return summary


def summary_cache(cache, source_sha256):
    if cache['source_sha256']!=source_sha256: raise ValueError('Summary belongs to different source bytes')
    if not cache.get('modules'): raise ValueError('Missing module summaries')
    for module in cache['modules']:
        if not isinstance(module.get('name'), str) or not module['name'].strip():
            raise ValueError('Missing module name')
        summary_fields(module['summary'], MODULE_FIELDS)
    summary_fields(cache['design_summary'], DESIGN_FIELDS)
    embedding=cache['embedding']
    if len(embedding)!=384 or any(type(v) not in (int,float) or not math.isfinite(v) for v in embedding):
        raise ValueError('Expected finite 384-dimensional all-MiniLM-L6-v2 embedding')
    if not math.isclose(sum(v*v for v in embedding), 1.0, abs_tol=1e-5):
        raise ValueError('Embedding must have L2 unit norm for comparable inner products')
    for field in ['summary_model','summary_model_revision','embedding_model','embedding_model_revision',
                  'prompt_sha256','embedding_normalization','embedding_truncation','generation_provenance']:
        if not cache.get(field): raise ValueError('Missing model provenance '+field)
    return embedding


def proposal(response, context):
    # Legal free-tool options only. This cannot validate unreleased industrial options.
    if not isinstance(response, dict) or set(response) != {'configuration'}:
        raise ValueError('Expected exact proposal envelope')
    chosen=response['configuration']
    if not isinstance(chosen, dict) or set(chosen)!={'mode','noalumacc'} or type(chosen['noalumacc']) is not bool:
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
