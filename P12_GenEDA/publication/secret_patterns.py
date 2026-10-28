"""Recovery-package pattern scan. Never prints matched secret values.

This is a bounded credential-pattern inspection, not a proof that arbitrary
unknown secrets are absent. It expands gzip and ZIP/NPZ file contents.
"""
import gzip
import io
import re
import zipfile

PATTERNS = {
    'provider_secret_key': re.compile(rb'\b(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'aws_access_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'private_key_block': re.compile(rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\r\n]{32,}'),
    'jwt': re.compile(rb'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{16,}\b'),
    'credential_assignment': re.compile(rb'''(?i)(?:api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|password|passwd|secret[_-]?key)["']?\s*[:=]\s*["']([A-Za-z0-9_+./=-]{16,})["']'''),
    'authorization_bearer': re.compile(rb'(?i)authorization["\s:=]+Bearer\s+([A-Za-z0-9_+./=-]{20,})'),
    'authorization_basic': re.compile(rb'(?i)authorization["\s:=]+Basic\s+[A-Za-z0-9+/=]{20,}'),
    'cookie_header': re.compile(rb'(?i)(?:set-cookie|cookie)["\s:=]+[A-Za-z0-9_-]+=[A-Za-z0-9_+./=-]{20,}'),
    'environment_secret_assignment': re.compile(rb'(?i)(?:AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN|GITHUB_TOKEN|OPENAI_API_KEY|AZURE_OPENAI_API_KEY)\s*=\s*[A-Za-z0-9_+./=-]{16,}'),
}
PLACEHOLDERS = {b'REDACTED_UPSTREAM_CREDENTIAL', b'YOUR_API_KEY_HERE', b'YOUR_API_KEY', b'not_a_real_api_key'}


def matches(raw):
    found = []
    for rule, pattern in PATTERNS.items():
        for match in pattern.finditer(raw):
            begin, end = match.span(1) if rule in ['credential_assignment', 'authorization_bearer'] else match.span()
            value = raw[begin:end]
            if value in PLACEHOLDERS or len(set(value)) < 5:
                continue
            found.append({'rule': rule, 'start': begin, 'end': end})
    return found


def scan(raw, label, expand=True):
    findings = [{'location': label, **item} for item in matches(raw)]
    if expand and raw.startswith(b'\x1f\x8b'):
        try:
            findings += scan(gzip.decompress(raw), label + '::gzip', False)
        except (OSError, EOFError):
            pass
    if expand and raw.startswith(b'PK\x03\x04'):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for name in z.namelist():
                    if not name.endswith('/'):
                        findings += scan(z.read(name), label + '::zip/' + name, False)
        except zipfile.BadZipFile:
            pass
    return findings


def redact_text(raw):
    found = matches(raw)
    spans = []
    for item in sorted(found, key=lambda item: item['start']):
        if spans and item['start'] <= spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], item['end']))
        else:
            spans.append((item['start'], item['end']))
    for start, end in reversed(spans):
        raw = raw[:start] + b'REDACTED_UPSTREAM_CREDENTIAL' + raw[end:]
    return raw, len(spans)
