"""CROP integration with the external shared OpenRouter client.

No credential is extracted, copied or configured here. The shared module owns
transport, its live switch, project authorization, four slots and USD ledger.
This module has no direct HTTP transport or automatic retry/fallback.
"""
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import importlib.util
import json
from pathlib import Path
import time

from api_adapter import ModelAPIError

BASE_URL = 'https://openrouter.ai/api/v1'


def reservation_usd(pricing, model, max_tokens=640):
    """Caller-supplied confirmed *upper* rates, never guessed current prices."""
    if not isinstance(pricing, dict) or pricing.get('model') != model or pricing.get('confirmed_upper_bound') is not True or not pricing.get('source'):
        raise ModelAPIError('Confirmed model/provider upper pricing is required')
    try:
        rates = [Decimal(str(pricing[name])) for name in
                 ('input_usd_per_million', 'output_usd_per_million', 'request_fee_usd')]
    except (KeyError, InvalidOperation, TypeError, ValueError):
        raise ModelAPIError('Invalid model/provider pricing') from None
    if any(not rate.is_finite() or rate < 0 for rate in rates):
        raise ModelAPIError('Invalid model/provider pricing')
    value = (Decimal(4096) * rates[0] + Decimal(max_tokens) * rates[1]) / Decimal(1000000) + rates[2]
    if value <= 0:
        raise ModelAPIError('A positive conservative cost reservation is required')
    return str(value.quantize(Decimal('0.000000001'), rounding=ROUND_CEILING))


class SharedChatAPI:
    def __init__(self, client, *, run_id, pricing, token_counter, allow_network=False,
                 safe_error_type=()):
        self.client = client
        self.run_id = run_id
        self.project = 'crop'
        self.pricing = pricing
        self.token_counter = token_counter
        self.allow_network = allow_network
        self.safe_error_type = safe_error_type
        # public_settings excludes the key; do not inspect client.config._data.
        settings = client.config.public_settings()
        if 'api_key' in settings or settings.get('base_url') != BASE_URL:
            raise ModelAPIError('Shared public configuration/base URL is invalid')
        self.base_url = settings['base_url']
        self.model = settings.get('chat_model')
        if not isinstance(self.model, str) or '/' not in self.model or self.model in ('openrouter/auto', 'openrouter/free') or self.model.endswith(':free'):
            raise ModelAPIError('Shared fixed model ID is required')
        self.batch_id = settings.get('batch_id')
        self.attempts = 0
        # The installed public chat interface may not expose temperature yet.
        # Preserve truth in records; never claim temperature zero if it was not sent.
        # The current public chat() does not expose decoding options. Use the
        # SAME shared budgeted request core, not a separate HTTP client, so all
        # gates, slots, attempt caps and ledger reservations remain enforced.
        if not callable(getattr(client, '_request', None)):
            raise ModelAPIError('Shared budgeted request core is unavailable')
        self.temperature = 0
        self.decoding = 'temperature=0; reasoning.enabled=false via shared budgeted request core'
        reservation_usd(pricing, self.model)

    def complete(self, messages, max_tokens=640, byte_cap=18000):
        if not self.allow_network:
            raise ModelAPIError('Shared network execution is not authorized')
        settings = self.client.config.public_settings()
        if (settings.get('base_url'), settings.get('chat_model'), settings.get('batch_id')) != (self.base_url, self.model, self.batch_id):
            raise ModelAPIError('Shared model/service/batch changed; stop')
        if type(max_tokens) is not int or not 1 <= max_tokens <= 640:
            raise ModelAPIError('Completion token cap exceeded')
        if byte_cap not in (12000, 18000):
            raise ModelAPIError('Unsupported request byte cap')
        try:
            input_tokens = self.token_counter(messages)
        except Exception:
            raise ModelAPIError('Input token counting failed') from None
        if type(input_tokens) is not int or not 0 <= input_tokens <= 4096:
            raise ModelAPIError('Input token cap exceeded')
        payload = dict(model=self.model, messages=messages, max_tokens=max_tokens,
                       stream=False, provider={'allow_fallbacks': False}, temperature=0,
                       reasoning={'enabled': False}, response_format={'type': 'json_object'})
        wire_bytes = len(json.dumps(payload).encode())
        if wire_bytes > byte_cap:
            raise ModelAPIError('Request byte cap exceeded')
        bound = reservation_usd(self.pricing, self.model, max_tokens)
        if self.attempts >= 33:
            raise ModelAPIError('CROP shared attempt cap exhausted')
        self.attempts += 1  # failures/denials never reset or receive a hidden retry
        started = time.monotonic()
        kwargs = dict(project=self.project, run_id=self.run_id,
                      max_cost_usd=bound, authorize_live=True)
        try:
            result = self.client._request('chat', payload, **kwargs)
        except Exception as exc:
            # SafeError messages are constants/status codes by the shared contract.
            detail = str(exc) if isinstance(exc, self.safe_error_type) else type(exc).__name__
            raise ModelAPIError('Shared request stopped: ' + detail + '; no retry') from None
        record = dict(seconds=time.monotonic()-started, request_model=self.model,
                      max_tokens=max_tokens, temperature=self.temperature, decoding=self.decoding,
                      input_tokens_counted=input_tokens, request_bytes=wire_bytes,
                      cost_reservation_usd=bound, project_attempt=self.attempts,
                      provider_fallbacks_requested=False, shared_project=self.project,
                      shared_run_id=self.run_id)
        try:
            choice = result['choices'][0]
            content = choice['message']['content']
            actual_model = result.get('model', self.model)
            if not isinstance(content, str) or not isinstance(actual_model, str):
                raise ValueError()
            raw_usage = result.get('usage') or {}
            usage = {k: v for k, v in raw_usage.items()
                     if k in ('prompt_tokens', 'completion_tokens', 'total_tokens')
                     and type(v) is int and v >= 0}
            record.update(raw_output=content, model=actual_model, usage=usage,
                          finish_reason=choice.get('finish_reason'))
            details = raw_usage.get('completion_tokens_details')
            if isinstance(details, dict) and type(details.get('reasoning_tokens')) is int:
                record['reasoning_tokens'] = details['reasoning_tokens']
            if isinstance(result.get('id'), str):
                record['response_id'] = result['id']
            if raw_usage.get('cost') is not None:
                cost = Decimal(str(raw_usage['cost']))
                if not cost.is_finite() or cost < 0:
                    raise ValueError()
                record['reported_cost_usd'] = str(cost)
        except (KeyError, IndexError, TypeError, ValueError, InvalidOperation):
            raise ModelAPIError('Shared provider completion schema invalid', evidence=record) from None
        if record['finish_reason'] != 'stop':
            raise ModelAPIError('Shared completion truncated or unfinished', evidence=record)
        if actual_model != self.model:
            raise ModelAPIError('Shared response model differs from the frozen model', evidence=record)
        if usage.get('prompt_tokens', 0) > 4096 or usage.get('completion_tokens', 0) > max_tokens:
            raise ModelAPIError('Shared provider token usage exceeded cap', evidence=record)
        return record


def load_shared_api(module_path, *, run_id, pricing, token_counter, allow_network=False,
                    _shared_module=None):
    """Future authorized entry only. Default blocks before loading private config.

    Tests inject a module with a fake load_config; they never invoke the real
    loader or read the user's private configuration/ledger.
    """
    if not allow_network:
        raise ModelAPIError('Shared loader is disabled before private configuration access')
    module = _shared_module
    if module is None:
        spec = importlib.util.spec_from_file_location('crop_shared_openrouter_runtime', Path(module_path))
        if spec is None or spec.loader is None:
            raise ModelAPIError('Shared OpenRouter module is unavailable')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    config = module.load_config()  # no key extraction, logging or repo-local copy
    return SharedChatAPI(module.Client(config), run_id=run_id, pricing=pricing,
                         token_counter=token_counter, allow_network=True,
                         safe_error_type=module.SafeError)
