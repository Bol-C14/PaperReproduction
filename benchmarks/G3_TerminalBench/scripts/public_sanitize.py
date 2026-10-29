"""Public views remove execution-host paths; private evidence remains byte-identical."""
import re


def public_text(text, source_root=None):
    if source_root:
        text = text.replace(source_root, '${REPRO_ROOT}')
    text = re.sub(r'/(?:home|Users)/[^/\s\x22\x27\\<>`]+', '${HOST_HOME}', text)
    text = re.sub(r'/tmp/tmp[a-zA-Z0-9_]+', '${TMPDIR}', text)
    text = re.sub(r'user-\d+\.slice', 'user-UID.slice', text)
    text = re.sub(r'user@\d+\.service', 'user@UID.service', text)
    return text


def public_view(value, source_root=None):
    if isinstance(value, str):
        return public_text(value, source_root)
    if isinstance(value, list):
        return [public_view(v, source_root) for v in value]
    if isinstance(value, dict):
        return {public_text(k, source_root): public_view(v, source_root) for k,v in value.items()}
    return value
