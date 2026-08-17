from __future__ import annotations

from .config import TESTED_DRAFT_LIBRARY_VERSION, TESTED_JIANYING_VERSION


CAPABILITIES = {
    "verified": [
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
    ],
    "partial_or_disabled": {
        "mask": "pyJianYingDraft 0.3.0 可写结构，但剪映 10.0.5 未显示；首版禁用",
        "blur_background": "结构可写但实测未显示；首版禁用",
        "audio_volume_keyframes": "结构可写但界面未观察到；首版禁用",
        "encrypted_reference_draft": "没有经源码审计的读取器；拒绝解析",
        "video_semantic_understanding": "已提供代表帧与字幕上下文；准确度取决于所用多模态模型和采样密度",
        "automatic_caption_or_transcript": "支持旁挂 SRT/VTT 和可选 Groq/OpenAI Whisper 语句级转写；尚非逐字强制对齐",
    },
    "not_in_v1": {
        "jianying_builtin_music_and_sfx": "需要剪映 UI/账号/在线资源自动化",
        "jianying_tts": "需要剪映 UI 与云端服务",
        "beat_detection_and_auto_cut": "需要剪映 UI 或独立音频分析器",
        "automatic_export": "剪映 7+ 隐藏控件，现有开源控制器不稳定",
    },
    "tested_versions": {
        "jianying": TESTED_JIANYING_VERSION,
        "pyJianYingDraft": TESTED_DRAFT_LIBRARY_VERSION,
    },
}


def capability_report() -> dict[str, object]:
    return CAPABILITIES
