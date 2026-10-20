# 与 jianying-editor-skill 的对照

本文对照本仓库与 [luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) v1.7.0，供剪刀组判断要不要在隔离仓库里做实验。本文不改 MCP 行为、能力声明或依赖。

查阅日：2026-10-20。对方版本以当天 `main` 上的 `VERSION`（`1.7.0`）、README 更新日志「v1.7（2026-09-11）」和仓库推送时间（2026-09-11）为准，公开 star 约 4300。之后对方再推送，以新的公开文本为准，本文不自动跟随。

## 对照对象

| | 本仓库 | 对方 |
|---|---|---|
| 仓库 | stupidearbre/jianying-ai-mcp（fork of Xanthus-Sanslab/jianying-ai-mcp） | [luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) |
| 形态 | stdio MCP + Skill | Agent Skill + Python 脚本，不是 MCP |
| 草稿库 | 依赖声明 pin 在 pyJianYingDraft `0.3.1` | `scripts/vendor/` 内嵌并二次开发 pyJianYingDraft |
| 调用方式 | Agent 提交编辑清单，MCP 按清单写草稿 | Agent 在业务目录写脚本，调用 `JyProject` 后 `save()` |

## 架构

本仓库把规划、观察和执行分开。Skill（`skills/jianying-ai-editor/`）负责需求引导和紧凑编辑清单。视频观察器负责本地元数据、字幕和代表帧。MCP（`src/jianying_ai_mcp/`）负责确定性生成、参考草稿复用、批量换料、安全校验和阶段进度。

MCP 工具：

- `get_jianying_capabilities`
- `analyze_reference_draft`
- `build_draft`
- `build_from_reference`
- `batch_from_template`
- `analyze_video_source`
- `save_video_observations`
- `get_video_analysis_context`

对方的入口是 `SKILL.md` 和 `scripts/jy_wrapper.py` 导出的 `JyProject`。约定写在 Skill 里：业务脚本放在用户当前项目，不放进 Skill 安装目录；脚本把 `scripts/` 加进路径后 `from jy_wrapper import JyProject`。这是给 Agent 调用的 Python 封装，没有与本仓库对等的 stdio 工具面。安装方式是把仓库克隆进 Cursor、Claude Code、Trae、Antigravity 各自的 skills 目录。

## 草稿格式与版本口径

本仓库通过 pyJianYingDraft `0.3.1` 写 `draft_content.json`。版本 profile 有两档：

- `10.0.5.13816`：已验证基线。
- `11.6.0.14552`：核心效果项已于 2026-10-18（Asia/Shanghai）由 wy 人工黑盒通过。通过项是打开预览，以及转场、滤镜、特效、动画、变速、关键帧、独立轨、混合模式。贴纸、字体、气泡花字、模板换料换字未测；导出未系统做。正式替换须可回退。记录见 [jianying_11_6_blackbox_checklist.md](jianying_11_6_blackbox_checklist.md)。

蒙版、模糊背景、音量关键帧在两个 profile 上都拒绝写入。能力类型见 [capability_matrix.md](capability_matrix.md)。该清单开头仍把 `11.6.0.14552` 写成「待黑盒回归」；通过记录以 README 和黑盒清单为准，本对照不改那份清单。

加密草稿只走既有 `jy-draftc`：复制到一次性工作目录，明文用完即删，不原地改写参考稿。这个只读路径不为 11.6 加强，也不把 11.6 的加密读取标成已适配。

对方公开口径集中在剪映 5.9+ / 6.x+ 的 `draft_info.json`：

- v1.7 修 5.9+「检测到媒体丢失」：外部素材暂存进草稿目录，`local_material_id` 保持稳定且非空。云音乐下载失败就报错，不再写入失效的虚拟路径。
- macOS：探测较新的草稿根目录；缺少 pymediainfo 时用 ffprobe；非标分辨率先做规整，避免剪映解析崩溃。
- 自动导出走 Windows UI Automation。对方写明剪映 5.9 及更低最稳，更高版本可能被弹窗或控件变化打断；macOS 只生成草稿，导出要在剪映里手动完成。
- README、v1.7 更新日志和 `SKILL.md` 没有 `11.6.0.14552` 的黑盒结论。

两边都站在 pyJianYingDraft 上，版本宣称的对象不同。本仓库把界面结论绑在 `10.0.5.13816` 和 `11.6.0.14552` 上。对方把草稿生成绑在 5.9+ 的 `draft_info.json`，把自动导出绑在 5.9 及更低。对方的 5.9 修复不能写成我们已经覆盖 11.6；我们的 11.6 核心项通过也不能写成对方测过这一版。

## 安全默认

本仓库：

- 工具默认 `dry_run=true`。草稿在暂存区生成并校验，不发布到剪映目录。用户明确要求正式生成时才 `dry_run=false`。
- 正式发布不覆盖同名草稿。测试名使用前缀 `TEST-laowang-`，只新建。
- 目标目录存在 `.locked` 时拒绝替换。
- 剪刀组一次只开一个剪映、一个 MCP。

对方公开用法：

- 快速开始和自修复示例使用 `JyProject(..., overwrite=True)`。同名工程按这个参数会被覆盖后重写。
- `save()` 把草稿写进剪映草稿目录。公开材料里没有与 `dry_run` 对等的默认闸门。
- 自动导出模拟键鼠。文档要求导出过程中不要操作鼠标和键盘。
- v1.5 更新日志写了路径穿越防护，避免非法路径写出技能目录之外的本机文件。

因此对方仓库不能原样接到剪刀组正在使用的草稿目录上。

## 对方有、本仓库没有

下列能力出现在对方 README 或更新日志里。本仓库的当前边界没有对应工具，也不操作剪映里的同类按钮：

- 智能配音字幕：文案生成语音再逐句对齐字幕，音色包括剪映原生音色和微软语音（`add_narrated_subtitles`）。
- 云音乐索引：`build_cloud_music_library.py` 从历史草稿挖掘用过的云端音乐 ID，供后续脚本推荐。
- 录屏和智能变焦：录下操作，对鼠标点击做推进和红圈。
- Web-to-Video：用 Playwright 录 HTML/Canvas 动效，再把视频导入时间轴。
- 复合片段。
- 影视解说，以及 v1.4 起按旁白语义从素材库挑画面。
- Windows 上的自动导出。
- 把 macOS 草稿目录、ffprobe 回退和 5.9+ 素材自包含当成已发布修复。

## 本仓库有、对方公开材料未写成同等物

- 固定的 MCP 工具契约。编辑清单进去，草稿出来。Agent 不逐片段改 JSON，也不为每一次剪辑新写一套业务脚本。
- 默认试运行、不覆盖同名、`.locked` 拒绝，以及测试名前缀。
- 两个版本 profile，以及 `11.6.0.14552` 核心效果项的具名黑盒记录（确认人 wy，2026-10-18）。
- 参考草稿分析、按轨道或片段换料换字、一个模板批量出多份草稿。
- 加密草稿只读。读取器是审计过的 `jy-draftc`，调用本机剪映目录里的 `videoeditor.dll`，不分发该 DLL。
- 视频观察和草稿执行分开：旁挂 SRT/VTT、可选的 Whisper 语句级转写、带时间戳的代表帧。只有无字幕且配置了 Key 时才上传压缩音频。Whisper 是外部转写，不是剪映内置识别。

## 共同不做

两边都没有把下列剪映内置能力做成可编程交付：

1. 剪映内置语音识别字幕（智能文本 / ASR）。对方写明语音识别字幕这类 GPU 实时能力目前无法用代码调用。本仓库的旁挂字幕和可选 Whisper 只做外部转写，README 写明不等同于剪映内置字幕识别。
2. 一键成片、图文成片一类界面 AI。对方写明这类按钮暂时不能自动触发。本仓库不操作这些界面功能。
3. 智能抠图、美颜等要剪映自己做实时处理的效果。对方明确做不到。本仓库没有对应的草稿写入接口。

对方还写明不支持 CapCut 国际版和手机端剪映。本仓库的交付对象是桌面剪映专业版草稿，这两端同样不在交付范围内。

## 团队建议

剪刀组（剪剪、二号、三号、四号）的生产继续用本 MCP + Skill。不要用 jianying-editor-skill 整仓替换。

生产路径依赖默认试运行、不覆盖、`.locked`、`TEST-laowang-`，以及已经记下的 `10.0.5.13816` / `11.6.0.14552` profile。对方的主路径是业务脚本直接 `save()`，示例带 `overwrite=True`，自动导出还要独占剪映窗口。两套默认放进同一个正在使用的草稿库会撞车。

对方适合当功能样本：看它怎样修 5.9 的媒体丢失，以及怎样把外部配音和网页动效送进时间轴。样本进入正式安装之前，单独开隔离仓库，并得到 wy 的同意。

## 可借鉴清单

状态：隔离实验。只允许在与剪刀组正式安装分开的仓库和草稿目录里试。未得到 wy 同意，不合并进本仓库的运行时代码，不改 `get_jianying_capabilities` 的能力声明，不加 pyproject 依赖。

1. 外部 TTS，产出音频轨和对齐字幕。优先 edge-tts 或微软语音，把成品音频和字幕当普通素材交给现有 `build_draft`。不绑定剪映内置 TTS，也不去点剪映里的字幕朗读。
2. 从历史明文草稿，或本机已经能只读解开的草稿里，抽取云音乐 `resource_id`，做成离线索引。账号、会员和版权都有风险：索引只覆盖该账号草稿里已经出现过的曲子，不能当成可再分发的曲库，也不能用来绕过会员。
3. Web-to-Video。用 Playwright 把 HTML 动效录成视频文件，再作为本地素材入轨。录制进程和剪映分开。产物仍走试运行和 `TEST-laowang-` 前缀。
4. 录屏智能变焦。这是教程视频的镜头处理，和剪刀组的粗剪主线关系弱。可以单独做素材预处理，不进入 MCP 的默认工具面。
5. 自动导出：默认不借鉴。它要抢剪映的键鼠，和「一次只开一个剪映」冲突。对方写明 5.9 及更低最稳，更高版本受弹窗和控件变化影响；按团队口径，剪映 7 及以上也不把自动导出当成默认。导出仍由人在剪映里完成。
