from __future__ import annotations

import inspect

import src.video_pipeline.astronomy.provider as provider_module


def test_provider_source_has_no_network_client_or_default_loader() -> None:
    source = inspect.getsource(provider_module)

    for forbidden in (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "urllib.request",
        "urlopen(",
        ".download(",
        "load(",
    ):
        assert forbidden not in source

    assert "load_file(" in source
    assert "timescale(builtin=True)" in source


def test_provider_never_accepts_url_or_download_configuration() -> None:
    signature = inspect.signature(provider_module.SkyfieldEphemerisProvider.from_local_ephemeris)
    assert "url" not in signature.parameters
    assert "download" not in signature.parameters
