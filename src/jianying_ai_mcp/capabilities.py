from __future__ import annotations

from .config import (
    JIANYING_PROFILES,
    TESTED_DRAFT_LIBRARY_VERSION,
    TARGET_JIANYING_VERSION,
    VERIFIED_JIANYING_VERSION,
    Settings,
    detected_jianying_version,
    profile_for_version,
)
from .draft_crypto import crypto_status


NOT_IN_V1 = {
    "jianying_builtin_music_and_sfx": "需要剪映 UI/账号/在线资源自动化",
    "jianying_tts": "需要剪映 UI 与云端服务",
    "beat_detection_and_auto_cut": "需要剪映 UI 或独立音频分析器",
    "automatic_export": "剪映 7+ 隐藏控件，现有开源控制器不稳定",
}

_ENCRYPTED_VERIFIED = (
    "read_encrypted_reference_draft",
    "copy_replace_and_batch_encrypted_template",
)


def _profile_summary(profile_version: str) -> dict[str, object]:
    profile = JIANYING_PROFILES[profile_version]
    return {
        "version": profile.version,
        "verification": profile.verification,
        "summary": profile.summary,
        "ui_evidence": profile.ui_evidence,
        "verified": list(profile.verified_capabilities),
        "pending_blackbox": list(profile.pending_blackbox_capabilities),
        "candidates": dict(profile.candidates),
        "partial_or_disabled": dict(profile.disabled),
        "risks": list(profile.risks),
    }


def capability_report(settings: Settings | None = None) -> dict[str, object]:
    detected = detected_jianying_version(settings) if settings is not None else None
    profile = profile_for_version(detected)
    if profile is None and detected is None:
        documented = JIANYING_PROFILES[VERIFIED_JIANYING_VERSION]
        status = "undetected"
        verified = list(documented.verified_capabilities)
        pending: list[str] = []
        disabled = dict(documented.disabled)
        candidates: dict[str, str] = {}
        verified_scope: str | None = documented.version
    elif profile is None:
        documented = JIANYING_PROFILES[VERIFIED_JIANYING_VERSION]
        status = "unlisted"
        verified = []
        pending = list(documented.verified_capabilities)
        disabled = dict(documented.disabled)
        candidates = {}
        verified_scope = None
    else:
        status = profile.verification
        verified = list(profile.verified_capabilities)
        pending = list(profile.pending_blackbox_capabilities)
        disabled = dict(profile.disabled)
        candidates = dict(profile.candidates)
        verified_scope = profile.version if profile.verification == "verified" else None

    report: dict[str, object] = {
        "active_profile": profile.version if profile else None,
        "profile_status": status,
        "verified_scope": verified_scope,
        "verified": verified,
        "pending_blackbox": pending,
        "candidates": candidates,
        "partial_or_disabled": disabled,
        "not_in_v1": dict(NOT_IN_V1),
        "profiles": {version: _profile_summary(version) for version in JIANYING_PROFILES},
        "tested_versions": {
            "jianying_verified_baseline": VERIFIED_JIANYING_VERSION,
            "jianying_target_pending_blackbox": TARGET_JIANYING_VERSION,
            "pyJianYingDraft": TESTED_DRAFT_LIBRARY_VERSION,
        },
        "production_replacement_requires": "wy 批准",
    }
    if settings is not None:
        encrypted = crypto_status(settings)
        report["encrypted_draft_reader"] = encrypted
        if encrypted["available"] and status == "verified":
            verified.extend(_ENCRYPTED_VERIFIED)
        elif encrypted["available"]:
            note = str(disabled.get("encrypted_reference_draft", ""))
            disabled["encrypted_reference_draft"] = (
                note + " 本机读取器可见，但当前 profile 不把它计入已验证能力。"
            ).strip()
    return report
