import os
from pathlib import Path

import pytest

import src.config.settings as settings_module

from src.config.settings import (
    SettingsError,
    load_kb_search_endpoint,
    load_settings,
    require_api_key,
    resolve_kb_search_config_path,
)


def _write_config(path: Path) -> None:
    path.write_text(
        """
app:
  env: development
  debug: false
  log_level: INFO
  timezone: UTC
  default_limit: 8
kb_search:
  base_url: ""
  api_port: 8008
  api_key: ""
  default_collection: local_kb_default
  timeout_seconds: 20
knowledge_base:
  sources_root: ./data/sources
  enable_obsidian_source: true
  obsidian_root: ./data/obsidian
  obsidian_ingest_source_label: obsidian
  obsidian_source_root_label: kaiyuan_zhanjing
astro:
  default_epoch: J2000
  default_lon: 116.4
  default_lat: 39.9
  default_location_name: Beijing
  visibility_min_alt_deg: 5
contract: {}
evidence: {}
cli: {}
logging: {}
paths: {}
postgres: {}
git_internal: {}
""",
        encoding="utf-8",
    )


def test_base_url_priority(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    monkeypatch.setenv("KB_SEARCH_BASE_URL", "http://localhost:9999")
    monkeypatch.setenv("KB_SEARCH_API_PORT", "8008")
    s = load_settings(cfg)
    assert s.kb_search_effective_base_url == "http://localhost:9999"


def test_port_fallback_when_base_url_missing(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    monkeypatch.delenv("KB_SEARCH_BASE_URL", raising=False)
    monkeypatch.setenv("KB_SEARCH_API_PORT", "8011")
    s = load_settings(cfg)
    assert s.kb_search_effective_base_url == "http://127.0.0.1:8011"


def test_require_api_key_raises_when_missing(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    monkeypatch.delenv("KB_SEARCH_API_KEY", raising=False)
    s = load_settings(cfg)
    try:
        require_api_key(s)
        raise AssertionError("expected SettingsError")
    except SettingsError as exc:
        assert "KB_SEARCH_API_KEY" in str(exc)


def test_env_overrides_yaml(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    monkeypatch.setenv("APP_DEFAULT_LIMIT", "13")
    monkeypatch.setenv("KB_SEARCH_TIMEOUT_SECONDS", "9")
    s = load_settings(cfg)
    assert s.app_default_limit == 13
    assert s.kb_search_timeout_seconds == 9.0


@pytest.mark.parametrize(
    ("setting", "environment_name", "original"),
    [
        ("default_lon", "ASTRO_DEFAULT_LON", "116.4"),
        ("default_lat", "ASTRO_DEFAULT_LAT", "39.9"),
        ("visibility_min_alt_deg", "ASTRO_VISIBILITY_MIN_ALT_DEG", "5"),
    ],
)
def test_huge_astronomy_float_settings_preserve_overflow_failure(
    monkeypatch,
    tmp_path: Path,
    setting: str,
    environment_name: str,
    original: str,
):
    """Catches an S1-only timeout accommodation widening global float parsing."""

    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            f"  {setting}: {original}",
            f"  {setting}: {'9' * 400}",
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv(environment_name, raising=False)

    with pytest.raises(OverflowError):
        load_settings(cfg)


def test_default_config_resolution_is_module_derived_and_cwd_independent(
    monkeypatch,
    tmp_path: Path,
):
    """Catches resolving the default configuration relative to process CWD."""

    monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
    repository_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repository_root)
    from_repository = resolve_kb_search_config_path()

    monkeypatch.chdir(tmp_path)
    from_unrelated_directory = resolve_kb_search_config_path()

    assert from_repository == from_unrelated_directory
    assert from_repository == (
        Path(__file__).resolve().parents[1] / "config" / "config.yaml"
    )
    assert from_repository.is_absolute()


def test_explicit_then_nonempty_environment_config_path_precedence(
    monkeypatch,
    tmp_path: Path,
):
    """Catches APP_CONFIG_PATH overriding an explicit internal factory path."""

    explicit = tmp_path / "explicit.yaml"
    environment = tmp_path / "environment.yaml"
    _write_config(explicit)
    _write_config(environment)
    monkeypatch.setenv("APP_CONFIG_PATH", str(environment))

    assert resolve_kb_search_config_path(explicit) == explicit.resolve()
    assert resolve_kb_search_config_path() == environment.resolve()
    monkeypatch.setenv("APP_CONFIG_PATH", "")
    assert resolve_kb_search_config_path() != environment.resolve()


def test_endpoint_only_loader_preserves_base_url_and_port_precedence(
    monkeypatch,
    tmp_path: Path,
):
    """Catches endpoint preflight depending on full Settings construction."""

    cfg = tmp_path / "config.yaml"
    _write_config(cfg)

    monkeypatch.setenv("KB_SEARCH_BASE_URL", "http://127.0.0.1:9101")
    monkeypatch.setenv("KB_SEARCH_API_PORT", "9102")
    assert load_kb_search_endpoint(cfg.resolve()) == "http://127.0.0.1:9101"

    monkeypatch.delenv("KB_SEARCH_BASE_URL")
    assert load_kb_search_endpoint(cfg.resolve()) == "http://127.0.0.1:9102"

    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            '  base_url: ""',
            '  base_url: "http://[::1]:9201/"',
        ),
        encoding="utf-8",
    )
    assert load_kb_search_endpoint(cfg.resolve()) == "http://[::1]:9201/"


def test_endpoint_only_loader_never_interpolates_api_key(
    monkeypatch,
    tmp_path: Path,
):
    """Catches endpoint parsing looking up a credential-bearing config field."""

    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            '  api_key: ""',
            "  api_key: ${KB_SEARCH_API_KEY}",
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("KB_SEARCH_API_KEY", raising=False)
    assert load_kb_search_endpoint(cfg.resolve()) == "http://127.0.0.1:8008"


def test_endpoint_only_loader_rejects_unsupported_endpoint_interpolation(
    monkeypatch,
    tmp_path: Path,
):
    """Catches unresolved endpoint placeholders reaching URL validation."""

    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            '  base_url: ""',
            "  base_url: ${UNSUPPORTED_ENDPOINT}",
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("UNSUPPORTED_ENDPOINT", raising=False)
    try:
        load_kb_search_endpoint(cfg.resolve())
    except SettingsError as exc:
        assert str(exc) == "Invalid KB Search endpoint configuration"
    else:  # pragma: no cover
        raise AssertionError("unsupported endpoint interpolation must fail")


def test_endpoint_only_loader_never_reads_credential_or_unsupported_variables(
    monkeypatch,
    tmp_path: Path,
):
    """Catches a field-agnostic interpolator reading attacker-selected secrets."""

    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    monkeypatch.setenv("KB_SEARCH_API_KEY", "unit-secret-must-not-be-read")
    monkeypatch.setenv("UNSUPPORTED_ENDPOINT", "http://127.0.0.1:9999")
    reads: list[str] = []

    class RecordingEnvironment(dict[str, str]):
        def __contains__(self, name: object) -> bool:
            reads.append(str(name))
            return super().__contains__(name)

        def __getitem__(self, name: str) -> str:
            reads.append(name)
            return super().__getitem__(name)

        def get(self, name: str, default: str | None = None) -> str | None:
            reads.append(name)
            return super().get(name, default)

    monkeypatch.setattr(
        settings_module.os,
        "environ",
        RecordingEnvironment(os.environ),
    )

    for placeholder in (
        "${KB_SEARCH_API_KEY}",
        "${UNSUPPORTED_ENDPOINT:-http://127.0.0.1:8008}",
    ):
        cfg.write_text(
            cfg.read_text(encoding="utf-8").replace(
                '  base_url: ""',
                f"  base_url: {placeholder}",
            ),
            encoding="utf-8",
        )
        try:
            load_kb_search_endpoint(cfg.resolve())
        except SettingsError as exc:
            assert str(exc) == "Invalid KB Search endpoint configuration"
        else:  # pragma: no cover
            raise AssertionError("unsupported endpoint variables must fail")
        cfg.write_text(
            cfg.read_text(encoding="utf-8").replace(
                f"  base_url: {placeholder}",
                '  base_url: ""',
            ),
            encoding="utf-8",
        )

    assert "KB_SEARCH_API_KEY" not in reads
    assert "UNSUPPORTED_ENDPOINT" not in reads


def test_endpoint_only_loader_accepts_only_field_specific_endpoint_forms(
    monkeypatch,
    tmp_path: Path,
):
    """Catches rejecting the repository's two supported endpoint placeholders."""

    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    cfg.write_text(
        cfg.read_text(encoding="utf-8")
        .replace('  base_url: ""', "  base_url: ${KB_SEARCH_BASE_URL:-}")
        .replace("  api_port: 8008", "  api_port: ${KB_SEARCH_API_PORT:-8123}"),
        encoding="utf-8",
    )
    monkeypatch.delenv("KB_SEARCH_BASE_URL", raising=False)
    monkeypatch.delenv("KB_SEARCH_API_PORT", raising=False)
    assert load_kb_search_endpoint(cfg.resolve()) == "http://127.0.0.1:8123"

    monkeypatch.setenv("KB_SEARCH_BASE_URL", "http://[::1]:9123")
    assert load_kb_search_endpoint(cfg.resolve()) == "http://[::1]:9123"
