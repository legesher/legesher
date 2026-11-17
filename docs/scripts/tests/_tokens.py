"""Token-stream comparison shared by the engine-drift and story round-trip tests."""

import io
import tokenize


def token_stream(code):
    return [
        (t.type, t.string)
        for t in tokenize.generate_tokens(io.StringIO(code).readline)
        if t.type not in (tokenize.ENCODING, tokenize.NL, tokenize.NEWLINE)
    ]
