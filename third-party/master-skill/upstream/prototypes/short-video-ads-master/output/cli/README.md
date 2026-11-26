# 短视频投流 CLI

把 短视频投流 master skill 的认知 OS 物化成 bash 工具。
不替代 SKILL.md（思维顾问），是它的「执行端」：交互问询 → 应用 playbook / protocol → 输出结构化报告。

## 用法

所有脚本支持 `--help` / `--explain` / `--dry-run` / `--json` 四个标准 flag。

```bash
# 拿到新问题时, 按 N 个研究维度做功课
./protocol/agentic.sh

# 决策树评估 (基于 playbook)
./decision/topic-1.sh
# SOP 走查 (workflow)
./workflow/50.sh

# 看背后的心智模型 / playbook (不交互)
./protocol/agentic.sh --explain
```

## 脚本清单

| 脚本 | 作用 |
|------|------|
| `protocol/agentic.sh` | Agentic Protocol (5 维度) — 拿到新问题时按这一行的研究维度做功课 |
| `decision/topic-1.sh` | 人群 决策树 (3 条规则) |
| `decision/topic-2.sh` | 创意 决策树 (2 条规则) |
| `decision/topic-3.sh` | 素材 决策树 (3 条规则) |
| `decision/general-playbook.sh` | 通用 Playbook 决策树 (1 条规则) |
| `workflow/50.sh` | 新计划冷启动 (前 50 转化) SOP 走查 |
| `workflow/3.sh` | 直播间投流 (3 阶段) SOP 走查 |
| `workflow/3.sh` | 创意素材生产 (黄金 3 秒法则) SOP 走查 |
| `workflow/5a-gta.sh` | 5A 人群 + GTA 方法论 (中大品牌) SOP 走查 |
| `workflow/11-618-38.sh` | 大促备战 (双 11 / 618 / 38 节) SOP 走查 |

## 设计与生成

CLI 子树由 `tools/cli_writer.py` 自动从 `references/synthesis.md` (Section 2 Playbook + Section 9 Agentic Protocol) 和 `references/research/03-workflows.md` 生成。

完整 spec 在 master-skill 仓库 `references/cli-spec.md`。

## 重新生成

如果 synthesis.md 或 03-workflows.md 更新了, 重跑:

```bash
python3 <master-skill>/tools/cli_writer.py emit \
  --skill-dir <this-skill-dir> \
  --synthesis references/synthesis.md \
  --workflows references/research/03-workflows.md \
  --industry-cn "短视频投流"
```
