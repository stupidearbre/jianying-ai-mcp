from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


VERIFIED_JIANYING_VERSION = "10.0.5.13816"
TARGET_JIANYING_VERSION = "11.6.0.14552"
TESTED_DRAFT_LIBRARY_VERSION = "0.3.1"
TEST_DRAFT_NAME_PREFIX = "TEST-laowang-"

# 这些能力只在 10.0.5.13816 上有界面结论。11.6 profile 复用同一份代码路径，
# 但必须标成待黑盒回归，不能把基线结论写成已在 11.6 实测。
_BASELINE_VERIFIED_CAPABILITIES: tuple[str, ...] = (
    "create_draft",
    "multi_track",
    "local_video_audio_image",
    "trim_and_speed",
    "audio_volume_and_fade",
    "srt_import",
    "text_style_border20_background_shadow",
    "transition",
    "video_filter_and_effect",
    "independent_filter_effect_tracks",
    "chroma_key_rgba",
    "mix_mode_and_overlay",
    "video_text_sticker_keyframes",
    "image_overlay_and_sticker",
    "font_bubble_flower_text",
    "text_video_animation",
    "audio_scene_tone_speech_to_song",
    "read_plaintext_reference_draft",
    "copy_replace_and_batch_plaintext_template",
    "local_video_metadata_and_representative_frames",
    "sidecar_srt_vtt_transcript",
    "cached_video_observation_report",
)

_SHARED_PARTIAL: dict[str, str] = {
    "blur_background": "结构可写，但剪映 10.0.5.13816 实测未显示；11.6.0.14552 待黑盒回归。两个 profile 都拒绝写入。",
    "audio_volume_keyframes": "结构可写，但剪映 10.0.5.13816 界面未观察到；11.6.0.14552 待黑盒回归。两个 profile 都拒绝写入。",
    "encrypted_reference_draft": (
        "加密模板读取依赖与剪映版本绑定的 jy-draftc 和 videoeditor.dll，有合规争议。"
        "本步不改加密读取路径，也不为 11.6 加强或新增解密能力。"
    ),
    "video_semantic_understanding": "已提供代表帧与字幕上下文；准确度取决于所用多模态模型和采样密度。",
    "automatic_caption_or_transcript": "支持旁挂 SRT/VTT 和可选 Groq/OpenAI Whisper 语句级转写；尚非逐字强制对齐。",
}


@dataclass(frozen=True)
class VersionProfile:
    version: str
    verification: str
    summary: str
    ui_evidence: str
    verified_capabilities: tuple[str, ...]
    pending_blackbox_capabilities: tuple[str, ...]
    disabled: dict[str, str]
    candidates: dict[str, str]
    risks: tuple[str, ...]


def _disabled_for_baseline() -> dict[str, str]:
    disabled = dict(_SHARED_PARTIAL)
    disabled["mask"] = (
        "剪映 10.0.5.13816 实测未显示。"
        "pyJianYingDraft 0.3.1 的蒙版修复只在剪映 5.9 与 10.8 验证过，不能据此在本基线上放开。"
    )
    return disabled


def _disabled_for_target() -> dict[str, str]:
    disabled = dict(_SHARED_PARTIAL)
    disabled["mask"] = (
        "11.6.0.14552 上的蒙版只登记为候选，写入仍然拒绝。"
        "pyJianYingDraft 0.3.1 已在剪映 5.9 与 10.8 修复新版蒙版，但 11.6 尚未黑盒回归。"
    )
    disabled["encrypted_reference_draft"] = (
        _SHARED_PARTIAL["encrypted_reference_draft"]
        + " 11.6 侧不要把读取器存在当成已适配。"
    )
    return disabled


JIANYING_PROFILES: dict[str, VersionProfile] = {
    VERIFIED_JIANYING_VERSION: VersionProfile(
        version=VERIFIED_JIANYING_VERSION,
        verification="verified",
        summary="现有基线。界面结论来自这一版剪映；依赖升到 pyJianYingDraft 0.3.1 后，界面尚未重跑。",
        ui_evidence="剪映专业版 10.0.5.13816，界面记录时使用 pyJianYingDraft 0.3.0。",
        verified_capabilities=_BASELINE_VERIFIED_CAPABILITIES,
        pending_blackbox_capabilities=(),
        disabled=_disabled_for_baseline(),
        candidates={},
        risks=(
            "在线字体、贴纸、动画和效果仍受账号、会员、缓存和网络影响。",
            "加密草稿读取只沿用既有只读副本流程，本步不扩展。",
            "正式环境替换前须 wy 批准。",
        ),
    ),
    TARGET_JIANYING_VERSION: VersionProfile(
        version=TARGET_JIANYING_VERSION,
        verification="pending_blackbox",
        summary="目标 profile。明文草稿仍由 pyJianYingDraft 写出；11.6 界面能力全部待黑盒回归，不能写成已实测。",
        ui_evidence="无。尚未在 11.6.0.14552 上做打开、预览、导出回归。",
        verified_capabilities=(),
        pending_blackbox_capabilities=_BASELINE_VERIFIED_CAPABILITIES,
        disabled=_disabled_for_target(),
        candidates={
            "mask": (
                "pyJianYingDraft 0.3.1 修复了新版剪映视频蒙版，发布说明写明已在剪映 5.9 与 10.8 验证。"
                "11.6.0.14552 没有实机结果，所以只作为候选，默认不开启写入。"
            ),
        },
        risks=(
            "在线资源 ID（特效、滤镜、动画、字体、气泡、花字、贴纸、文字模板）可能随版本下架或更换。",
            "加密模板读取有合规风险，并且和剪映版本强绑定。本步不实现、不加强加密读取。",
            "剪映打开并保存后草稿会被重新加密，生成后能打开不等于之后还能程序化修改。",
            "11.x 草稿 schema 没有公开文档。",
            "正式环境替换前须 wy 批准。这是测试仓改动，不要求正在使用的生产环境升级。",
        ),
    ),
}


@dataclass(frozen=True)
class Settings:
    draft_root: Path
    work_root: Path
    jianying_exe: Path | None
    ffmpeg_exe: Path | None = None
    ffprobe_exe: Path | None = None
    yt_dlp_exe: Path | None = None
    draft_crypto_exe: Path | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        draft_root = Path(
            os.environ.get(
                "JIANYING_DRAFT_ROOT",
                str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft"),
            )
        ).expanduser().resolve()
        work_root = Path(
            os.environ.get("JIANYING_MCP_WORK_ROOT", str(Path.cwd() / ".jianying-mcp"))
        ).expanduser().resolve()
        raw_exe = os.environ.get("JIANYING_EXE")
        exe = Path(raw_exe).expanduser().resolve() if raw_exe else _find_jianying_exe()
        return cls(
            draft_root=draft_root,
            work_root=work_root,
            jianying_exe=exe,
            ffmpeg_exe=_find_media_tool("ffmpeg", "JIANYING_FFMPEG"),
            ffprobe_exe=_find_media_tool("ffprobe", "JIANYING_FFPROBE"),
            yt_dlp_exe=_find_media_tool("yt-dlp", "JIANYING_YT_DLP"),
            draft_crypto_exe=_find_draft_crypto(),
        )


def _find_jianying_exe() -> Path | None:
    roots = [Path(os.environ.get("LOCALAPPDATA", "")) / "JianyingPro"]
    matches: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        matches.extend(root.glob("**/JianyingPro.exe"))
        direct = root / "JianyingPro.exe"
        if direct.is_file():
            matches.append(direct)
    if not matches:
        return None
    return sorted(matches, key=lambda path: _version_tuple(path.parent.name), reverse=True)[0].resolve()


def _find_media_tool(name: str, env_name: str) -> Path | None:
    configured = os.environ.get(env_name)
    if configured:
        path = Path(configured).expanduser().resolve()
        return path if path.is_file() else None

    found = shutil.which(name)
    if found:
        return Path(found).resolve()

    return None


def _find_draft_crypto() -> Path | None:
    configured = _find_media_tool("jy-draftc", "JIANYING_DRAFT_CRYPTO")
    if configured:
        return configured
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    candidates = [
        Path.cwd() / ".jianying-mcp" / "tools" / "jy-draftc.exe",
        local_app_data / "jianying-ai-mcp" / "bin" / "jy-draftc.exe",
    ]
    return next((path.resolve() for path in candidates if path.is_file()), None)


def _version_tuple(value: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", value)
    return tuple(int(num) for num in nums) if nums else (0,)


def detected_jianying_version(settings: Settings) -> str | None:
    if settings.jianying_exe is None:
        return None
    folder_version = settings.jianying_exe.parent.name
    return folder_version if re.fullmatch(r"\d+(?:\.\d+)+", folder_version) else None


def profile_for_version(version: str | None) -> VersionProfile | None:
    if version is None:
        return None
    return JIANYING_PROFILES.get(version)


def is_test_draft_name(name: str) -> bool:
    return name.startswith(TEST_DRAFT_NAME_PREFIX)


def blocked_feature_reason(feature: str, version: str | None) -> str | None:
    """需要拒绝写入时返回原因。蒙版在任何 profile 上都未默认放开。"""
    profile = profile_for_version(version)
    if feature == "mask":
        if profile is not None and "mask" in profile.candidates:
            return profile.candidates["mask"] + " 待黑盒回归前不写入。"
        if profile is not None and "mask" in profile.disabled:
            return profile.disabled["mask"]
        return (
            "mask 在已验证基线 10.0.5.13816 上未显示，11.6.0.14552 也只是未实测候选。"
            "默认不写入。"
        )
    if feature == "background_filling":
        return _SHARED_PARTIAL["blur_background"]
    if feature == "audio_volume_keyframes":
        return _SHARED_PARTIAL["audio_volume_keyframes"]
    return None


def compatibility_notice(settings: Settings) -> dict[str, object]:
    detected = detected_jianying_version(settings)
    profile = profile_for_version(detected)
    baseline = VERIFIED_JIANYING_VERSION
    target = TARGET_JIANYING_VERSION
    if detected is None:
        status = "undetected"
        message = (
            f"未检测到剪映版本。已登记 profile：{baseline}（已验证基线）、"
            f"{target}（待黑盒回归）。"
            "不能把基线界面结论套到未识别的安装上，生成后必须抽样确认。"
            "正式环境替换前须 wy 批准。"
        )
        risks = (
            "未命中已登记 profile 时，预设 ID 与草稿表现都需要抽检。",
            "正式环境替换前须 wy 批准。",
        )
    elif profile is None:
        status = "unlisted"
        message = (
            f"当前剪映 {detected} 不在已登记 profile（{baseline}、{target}）中。"
            "动画、在线资源、滤镜和草稿格式可能失效或显示不同，生成后必须抽样确认。"
            "正式环境替换前须 wy 批准。"
        )
        risks = (
            "未登记版本没有独立的已验证或待回归清单。",
            "在线资源 ID 与加密模板读取都不要假定可用。",
            "正式环境替换前须 wy 批准。",
        )
    elif profile.verification == "verified":
        status = "verified"
        message = (
            f"当前剪映 {detected} 命中已验证 profile。"
            f"草稿库为 pyJianYingDraft {TESTED_DRAFT_LIBRARY_VERSION}；"
            "该界面结论记录于 0.3.0，0.3.1 尚未在本版本重跑界面。"
            "蒙版、模糊背景和音量关键帧仍然禁用。"
        )
        risks = profile.risks
    else:
        status = "pending_blackbox"
        message = (
            f"当前剪映 {detected} 已登记为目标 profile，状态是待黑盒回归，不是已实测通过。"
            f"{baseline} 的界面结论不能直接当作 {detected} 的结果。"
            "在线资源 ID 可能失效；加密模板读取不在本步适配范围内，且有合规风险。"
            "生成后必须抽样确认。正式环境替换前须 wy 批准。"
        )
        risks = profile.risks
    return {
        "detected": detected,
        "profile": profile.version if profile else None,
        "profile_status": status,
        "tested": baseline,
        "verified_baseline": baseline,
        "registered_profiles": list(JIANYING_PROFILES),
        "matches_tested_version": status == "verified",
        "draft_library": TESTED_DRAFT_LIBRARY_VERSION,
        "production_replacement_requires": "wy 批准",
        "message": message,
        "risks": list(risks),
    }
