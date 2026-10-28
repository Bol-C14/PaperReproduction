"""OpenAI-compatible chat adapter; transport is disabled unless explicitly enabled.

The caller must supply a counter for the authorized model's complete chat input.
No tokenizer, credential, model or endpoint discovery is performed here.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


class ModelAPIError(RuntimeError):
    def __init__(self, message, evidence=None):
        super().__init__(message)
        self.evidence = evidence or {}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ModelAPIError('Provider redirect refused')


class ChatAPI:
    def __init__(self, allow_network=False, transport=None, token_counter=None):
        self.allow_network = allow_network
        self.transport = transport or urllib.request.build_opener(NoRedirect()).open
        self.token_counter = token_counter

    def complete(self, messages, max_tokens=640, byte_cap=18000):
        if not self.allow_network:
            raise ModelAPIError('Network is not authorized')
        base = os.environ.get('PAPER_LLM_BASE_URL', '').rstrip('/')
        key = os.environ.get('PAPER_LLM_API_KEY', '')
        model = os.environ.get('PAPER_LLM_MODEL', '')
        if not all([base, key, model]):
            raise ModelAPIError('Required runtime configuration missing')
        url = urllib.parse.urlsplit(base)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ModelAPIError('Expected a clean authorized HTTPS API base URL')
        if type(max_tokens) is not int or not 1 <= max_tokens <= 640:
            raise ModelAPIError('Completion token cap exceeded')
        if byte_cap not in (12000, 18000):
            raise ModelAPIError('Unsupported request byte cap')
        if self.token_counter is None:
            raise ModelAPIError('Authorized model chat token counter is required')
        try:
            input_tokens = self.token_counter(messages)
        except Exception:
            raise ModelAPIError('Input token counting failed') from None
        if type(input_tokens) is not int or not 0 <= input_tokens <= 4096:
            raise ModelAPIError('Input token cap exceeded')
        payload = {'model': model, 'messages': messages, 'temperature': 0,
                   'max_tokens': max_tokens, 'stream': False}
        data = json.dumps(payload).encode()
        if len(data) > byte_cap:
            raise ModelAPIError('Request byte cap exceeded')
        request = urllib.request.Request(base + '/chat/completions', data=data,
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}, method='POST')
        start = time.monotonic()
        try:
            with self.transport(request, timeout=180) as response:
                raw = response.read(1000001)
        except urllib.error.HTTPError as exc:
            raise ModelAPIError('Provider HTTP status ' + str(exc.code)) from None
        except Exception as exc:
            raise ModelAPIError('Provider transport failed: ' + type(exc).__name__) from None
        if len(raw) > 1000000:
            raise ModelAPIError('Response size cap exceeded')
        try:
            result = json.loads(raw)
            choice = result['choices'][0]
            content = choice['message']['content']
            if not isinstance(content, str):
                raise ValueError()
            usage = {name: value for name, value in result.get('usage', {}).items()
                     if name in ('prompt_tokens', 'completion_tokens', 'total_tokens')
                     and type(value) is int and value >= 0}
            actual_model = result.get('model', model)
            if not isinstance(actual_model, str):
                raise ValueError()
        except Exception:
            raise ModelAPIError('Provider response does not match completed chat schema') from None
        record = {'raw_output': content, 'usage': usage, 'seconds': time.monotonic() - start,
                'model': actual_model, 'request_model': model, 'max_tokens': max_tokens,
                'temperature': 0, 'input_tokens_counted': input_tokens, 'request_bytes': len(data),
                'finish_reason': choice.get('finish_reason')}
        if choice.get('finish_reason') != 'stop':
            raise ModelAPIError('Provider did not return completed chat schema', evidence=record)
        if usage.get('prompt_tokens', 0) > 4096 or usage.get('completion_tokens', 0) > max_tokens:
            raise ModelAPIError('Provider usage exceeded declared token budget; stop', evidence=record)
        return record
