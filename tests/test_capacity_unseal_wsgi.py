"""Wrapper EOF/exception cleanup only; mocked response, no integration claim."""
import json

import pytest

from tests import capacity_unseal_wsgi as wrapper


@pytest.mark.parametrize('marked', [False, True])
@pytest.mark.parametrize('failure', [False, True])
def test_original_response_is_closed_once(marked, failure, tmp_path, monkeypatch):
    class Response:
        closed = 0

        def __iter__(self):
            yield b'synthetic'
            if failure:
                raise RuntimeError('Synthetic stream failure')

        def close(self):
            self.closed += 1

    response = Response()
    monkeypatch.setattr(wrapper, 'original', lambda environ, start_response: response)
    output = tmp_path / 'report.json'
    monkeypatch.setenv('UNSEAL_DIAGNOSTIC_OUTPUT', str(output))
    environ = {'HTTP_X_UNSEAL_DIAGNOSTIC': 'one_batch'} if marked else {}
    if failure:
        with pytest.raises(RuntimeError, match='stream failure'):
            list(wrapper.application(environ, lambda *args: None))
    else:
        assert list(wrapper.application(environ, lambda *args: None)) == [b'synthetic']
    assert response.closed == 1
    if marked and not failure:
        assert json.loads(output.read_text())['unseal']['calls'] == 0
    else:
        assert not output.exists()
