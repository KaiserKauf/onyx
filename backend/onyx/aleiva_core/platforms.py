from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]
ProbeKind = Literal["http", "websocket"]


@dataclass(frozen=True)
class ProbeTarget:
    label: str
    url: str
    kind: ProbeKind = "http"


@dataclass(frozen=True)
class PlatformProfile:
    id: str
    display_name: str
    domains: tuple[str, ...]
    product_type: str
    risk_level: RiskLevel
    capabilities: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    default_onboarding_steps: tuple[str, ...]
    probe_targets: tuple[ProbeTarget, ...]
    external_repo_refs: tuple[str, ...]
    control_surface_url: str | None = None


_PLATFORM_REGISTRY: tuple[PlatformProfile, ...] = (
    PlatformProfile(
        id="aleivaos",
        display_name="AleivaOS",
        domains=("localhost:8080", "127.0.0.1:8080"),
        product_type="browser_os",
        risk_level="low",
        capabilities=("service_topology", "claw3d_control", "jarvis_chat"),
        allowed_actions=("start_local_services", "view_topology", "open_os_shell"),
        default_onboarding_steps=(
            "Run scripts/start_all_local.ps1 to start XAMPP and Jarvis services",
            "Open http://127.0.0.1:8080/os.html for the browser OS shell",
            "Open Claw3D control and verify unified status from Jarvis Bridge :8900",
            "Use Jarvis chat for operator commands — no live trading from AleivaOS",
        ),
        probe_targets=(
            ProbeTarget("AleivaOS shell", "http://127.0.0.1:8080/os.html"),
            ProbeTarget(
                "Jarvis unified status",
                "http://127.0.0.1:8900/v1/status/unified",
            ),
            ProbeTarget("Claw3D control", "http://127.0.0.1:8080/claw3d-control.html"),
        ),
        external_repo_refs=("vulty-trading-architecture",),
        control_surface_url="http://127.0.0.1:8080/os.html",
    ),
    PlatformProfile(
        id="vulty",
        display_name="Vulty",
        domains=("vulty.io", "vultify.com", "app.vulty.io"),
        product_type="cybersecurity_saas",
        risk_level="medium",
        capabilities=("signup", "pricing", "api_panel", "paper_trading_guidance"),
        allowed_actions=(
            "onboarding",
            "sandbox_api_connect",
            "dry_trading_analysis",
            "paper_execution_guidance",
        ),
        default_onboarding_steps=(
            "Create a Vulty profile via onboarding.html",
            "Choose paper/sandbox mode — live execution requires explicit approval",
            "Connect exchange API in read-only or sandbox mode only",
            "Run dry analysis and review risk gate before any paper order",
        ),
        probe_targets=(
            ProbeTarget("Jarvis SaaS health", "http://127.0.0.1:8001/api/health"),
            ProbeTarget("Jarvis bridge", "http://127.0.0.1:8900/health"),
            ProbeTarget("Onboarding", "http://127.0.0.1:8080/onboarding.html"),
        ),
        external_repo_refs=("vulty-trading-architecture", "Vulty", "VultyPro"),
        control_surface_url="http://127.0.0.1:8080/onboarding.html",
    ),
    PlatformProfile(
        id="aleiva-music",
        display_name="Aleiva Music",
        domains=("aleiva.de",),
        product_type="music_production",
        risk_level="low",
        capabilities=("project_setup", "content_workflow", "publishing_checklist"),
        allowed_actions=("create_project", "manage_tracks", "publish_checklist"),
        default_onboarding_steps=(
            "Set up a music production project workspace",
            "Define release checklist and asset pipeline",
            "No trading or cybersecurity actions on this platform",
        ),
        probe_targets=(),
        external_repo_refs=("Aleiva",),
        control_surface_url="https://aleiva.de",
    ),
    PlatformProfile(
        id="aleiva-quantum-trading",
        display_name="Aleiva Quantum Trading",
        domains=("aleiva-quantum-trading.com", "localhost:8501"),
        product_type="quant_trading_research",
        risk_level="high",
        capabilities=("paper_trading", "backtest_guidance", "metrics_dashboard"),
        allowed_actions=(
            "paper_execution",
            "sandbox_analysis",
            "view_metrics",
            "dry_run_strategy_review",
        ),
        default_onboarding_steps=(
            "Confirm paper/sandbox mode — live trading is blocked by default",
            "Review strategy thesis with dry-run analysis only",
            "Open Streamlit dashboard on :8501 for research metrics",
            "Use trading engine WebSocket :8765 for paper tick streams only",
        ),
        probe_targets=(
            ProbeTarget("Trading dashboard", "http://127.0.0.1:8501"),
            ProbeTarget("Trading engine health", "http://127.0.0.1:8100/health"),
            ProbeTarget("Trading WebSocket", "ws://127.0.0.1:8765", kind="websocket"),
            ProbeTarget("Prometheus", "http://127.0.0.1:9090/-/healthy"),
        ),
        external_repo_refs=("vulty-trading-architecture",),
        control_surface_url="http://127.0.0.1:8501",
    ),
)


def list_platforms() -> list[PlatformProfile]:
    return list(_PLATFORM_REGISTRY)


def get_platform(platform_id: str) -> PlatformProfile | None:
    normalized = platform_id.strip().lower()
    for platform in _PLATFORM_REGISTRY:
        if platform.id == normalized:
            return platform
    return None


def platform_guide(platform_id: str) -> dict[str, object] | None:
    platform = get_platform(platform_id)
    if platform is None:
        return None
    return {
        "platform_id": platform.id,
        "display_name": platform.display_name,
        "risk_level": platform.risk_level,
        "control_surface_url": platform.control_surface_url,
        "onboarding_steps": list(platform.default_onboarding_steps),
        "allowed_actions": list(platform.allowed_actions),
        "capabilities": list(platform.capabilities),
        "probe_targets": [
            {"label": probe.label, "url": probe.url, "kind": probe.kind}
            for probe in platform.probe_targets
        ],
        "trading_mode": (
            "paper_sandbox_only"
            if platform.id in {"vulty", "aleiva-quantum-trading"}
            else "not_applicable"
        ),
        "non_advice_notice": (
            "Outputs are guidance for human review only. Not financial advice."
            if platform.risk_level == "high"
            else None
        ),
    }
