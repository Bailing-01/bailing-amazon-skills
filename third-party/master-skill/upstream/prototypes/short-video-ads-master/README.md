# Prototype · 短视频投流

mini-viable 样本，验证商业 + 算法投放行业。

## 目录内容

| 路径 | 说明 |
|---|---|
| `intake.json` | 行业澄清结果 |
| `references/research/0X-*.md` | 6 路调研笔记（大部分占位，仅 03-workflows 完整） |
| `references/synthesis.md` | 蒸馏文档 |
| `output/SKILL.md` | 生成的 skill |
| `output/meta.json` | 元数据 |
| `output/cli/` | 自动生成的 bash 工具 |

## 蒸馏要点

- 3 心智模型：创意是因 / 出价是果，冷启动期 ROAS 低是常态，跑量 ≠ 跑利润
- 5 决策规则
- 3 研究维度（创意层 / 人群层 / 出价策略）
- 2 工作流：新计划冷启动 + 爆量计划日常优化

## 重新生成

```bash
python3 tools/skill_writer.py create \
  --skill-dir prototypes/short-video-ads-master/output \
  --intake prototypes/short-video-ads-master/intake.json \
  --synthesis prototypes/short-video-ads-master/references/synthesis.md \
  --template references/skill-template.md \
  --research-dir prototypes/short-video-ads-master/references/research
```
