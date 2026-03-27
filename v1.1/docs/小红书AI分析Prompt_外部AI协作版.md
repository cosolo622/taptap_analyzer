# 小红书AI分析 Prompt（外部AI协作版）

## 1. 使用说明

- 你把真实抓取数据按 JSON 数组给外部 AI。
- 让外部 AI 严格输出 JSON，不要输出解释文字。
- 先跑单条验证，再跑批量。

## 2. 单条分析 Prompt

```text
你是游戏社区舆情分析助手。请对下面这条小红书内容做结构化分析。

分析维度：
1) sentiment：仅可取 正向/负向/中性
2) topic：仅可取 玩法技巧/产品口碑/社区生态/版本活动/商业化反馈/其他
3) risk_level：仅可取 高/中/低
4) risk_reason：不超过30字
5) summary：不超过40字
6) importance_score：0-100 的整数

判定要求：
- 若出现辱骂、诈骗、严重负面舆情、封号集中反馈等，risk_level倾向高
- 若只是一般抱怨或争议，risk_level倾向中
- 常规攻略/日常分享，risk_level倾向低
- importance_score综合考虑互动量（点赞、评论、收藏、分享）和内容传播性

输入数据：
{{single_record_json}}

只输出 JSON，格式如下：
{
  "sentiment": "",
  "topic": "",
  "risk_level": "",
  "risk_reason": "",
  "summary": "",
  "importance_score": 0
}
```

## 3. 批量分析 Prompt（推荐）

```text
你是游戏社区舆情分析助手。请对输入数组中的每条小红书内容进行结构化分析。

字段要求：
- sentiment：正向/负向/中性
- topic：玩法技巧/产品口碑/社区生态/版本活动/商业化反馈/其他
- risk_level：高/中/低
- risk_reason：<=30字
- summary：<=40字
- importance_score：0-100整数

输入：
{{batch_records_json}}

输出要求：
1) 只输出 JSON 数组，不要任何解释
2) 输出顺序与输入顺序一致
3) 每条结果必须包含 record_id 字段，并与输入一致

输出示例：
[
  {
    "record_id": "xxx",
    "sentiment": "负向",
    "topic": "产品口碑",
    "risk_level": "中",
    "risk_reason": "集中反馈卡顿与掉线",
    "summary": "玩家集中吐槽卡顿掉线，体验受损",
    "importance_score": 78
  }
]
```

## 4. 热点话题追踪 Prompt

```text
你是社区热点分析助手。给你最近N小时的小红书舆情记录，请输出热点主题与变化判断。

目标：
1) 识别 TOP5 热点主题
2) 判断每个主题是 上升/持平/下降
3) 给出每个主题的一句话解读和建议动作

输入：
{{recent_records_json}}

只输出 JSON：
{
  "hot_topics": [
    {
      "topic": "",
      "trend": "上升",
      "volume": 0,
      "negative_ratio": 0.0,
      "insight": "",
      "action": ""
    }
  ]
}
```

## 5. 负面突增预警 Prompt

```text
你是舆情预警助手。根据当前窗口与历史基线输出预警判断。

输入：
{
  "window_hours": 4,
  "current_negative_count": 0,
  "baseline_negative_count": 0,
  "current_topic_breakdown": [],
  "baseline_topic_breakdown": []
}

规则：
- 当前负面量 >= 基线1.8倍 且 增量>=20，触发黄色预警
- 当前负面量 >= 基线2.5倍 且 增量>=40，触发橙色预警
- 若连续两个窗口超阈值，升级一级

只输出 JSON：
{
  "alert_level": "无/黄/橙/红",
  "triggered": false,
  "reason": "",
  "focus_topics": [],
  "recommended_actions": []
}
```
