from onyx.aleiva_core.platforms import get_platform
from onyx.aleiva_core.platforms import list_platforms
from onyx.aleiva_core.platforms import platform_guide


def test_list_platforms_includes_hybrid_targets() -> None:
    platforms = list_platforms()
    platform_ids = {platform.id for platform in platforms}
    assert platform_ids == {
        "aleivaos",
        "vulty",
        "aleiva-music",
        "aleiva-quantum-trading",
    }


def test_aleivaos_probe_targets_include_jarvis_bridge() -> None:
    platform = get_platform("aleivaos")
    assert platform is not None
    probe_urls = {probe.url for probe in platform.probe_targets}
    assert "http://127.0.0.1:8900/v1/status/unified" in probe_urls
    assert "http://127.0.0.1:8080/os.html" in probe_urls


def test_vulty_guide_is_paper_sandbox_first() -> None:
    guide = platform_guide("vulty")
    assert guide is not None
    assert guide["trading_mode"] == "paper_sandbox_only"
    assert any("paper" in step.lower() for step in guide["onboarding_steps"])


def test_unknown_platform_returns_none() -> None:
    assert get_platform("unknown-platform") is None
    assert platform_guide("unknown-platform") is None
