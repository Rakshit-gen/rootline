import os
from unittest import mock

from app.llm import MockLLMClient
from app.openai_client import OpenAIClient, get_llm_client


def test_defaults_to_mock_without_api_key():
    with mock.patch.dict(os.environ, {}, clear=True):
        assert isinstance(get_llm_client(), MockLLMClient)


def test_uses_real_client_when_api_key_present():
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        assert isinstance(get_llm_client(), OpenAIClient)


def test_openai_client_requires_a_key():
    with mock.patch.dict(os.environ, {}, clear=True):
        try:
            OpenAIClient()
            assert False, "expected KeyError"
        except KeyError:
            pass
