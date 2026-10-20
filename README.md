# GetOffer

帮助校招生和实习求职者从真实经历出发写改简历、按目标 JD 定制、准备面试并逐题复盘的 Agent Skill。当前版本：v1.3.2。

## 功能

- 写改简历：从零散经历整理个人贡献，生成通用简历。
- JD 定制：分析匹配情况，选择相关经历，生成岗位版简历。
- 面试准备：准备自我介绍、经历回答和逐轮模拟面试。
- 面试复盘：分析录音或文字稿，给出逐题改进答法，确认新素材后回写简历。

四个模块共用经历库，保留通用版、各岗位版本和旧稿。目标岗位不限产品经理，默认中文，也支持英文材料。

仅在材料存在缺口、需要帮助理解时，提供少量动作线索和简短回答样例；已有信息清楚时直接改稿。

## 安装

完整技能位于 [`skills/get-offer/`](skills/get-offer/SKILL.md)。将整个目录放入所用工具支持的技能目录，保留 `references/`、`assets/` 和 `agents/`。

macOS 或 Linux 可通过链接安装：

```sh
git clone https://github.com/beautfulmt/GetOffer.git "$HOME/GetOffer"
mkdir -p "$HOME/.codex/skills" "$HOME/.claude/skills"
ln -s "$HOME/GetOffer/skills/get-offer" "$HOME/.codex/skills/get-offer"
ln -s "$HOME/GetOffer/skills/get-offer" "$HOME/.claude/skills/get-offer"
```

目标已有同名目录或链接时，先备份再处理。按实际使用的工具选择对应安装位置。

## 使用

直接描述当前任务并提供已有材料，例如：

- “我没有实习，做过课程项目，帮我整理一份简历。”
- “按这份产品实习 JD 调整简历，缺什么也直接说。”
- “基于这份简历模拟一面，每次问一题。”
- “逐题复盘这段面试稿，给出完整改进答法。”

## 文件与能力

个人材料默认保存在 `~/get-offer-data/`，也可指定位置；明确要求不保存时，只在对话中处理。简历只使用用户明确陈述或确认的事实。

PDF、可编辑 Word 和录音转写依赖所用工具的现有能力。技能不自带转写引擎，不要求 API Key；能力不足或样式降级时会说明实际完成情况，上传第三方转写前需要用户同意。

仓库只提供技能入口、参考规则、模板与界面元数据，不包含个人求职材料或开发演练记录。
