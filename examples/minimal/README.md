# 最小示例 · 门缝（20 秒 / 4 镜）

一个可跑通校验的通用示例，题材是都市悬疑。用来验证脚手架与分镜字段，不是成片。

## 跑一遍

```bash
# 在仓库根目录
python3 templates/project/validate_shots.py examples/minimal/story.json
# → 镜头数 4 · 平均 5.00s · 景别分布 {'LS':1,'ECU':1,'MS':1,'CU':1}
# → 结果：0 error / 0 warning
```

## 接进项目

```bash
cp -R templates/project/* my-episode/
mkdir -p my-episode/design
cp examples/minimal/story.json my-episode/design/story.json
cd my-episode
python3 tools/validate_shots.py design/story.json
python3 tools/build_timeline.py        # 需要 macOS say + ffmpeg
```

`build_timeline.py` 会按实测配音重排镜头窗，并生成 `src/story.js`、`assets/audio/*.mp3`、`assets/subtitles/ep.srt`。

## 这四镜在示范什么

| 镜 | 示范点 |
|---|---|
| S1 LS 35mm 缓推 | 用长引导线建立"人到门"的距离；L-cut 把走廊底噪带进下一镜 |
| S2 ECU 85mm 固定 | 框中框（门缝）+ J-cut（呼吸先入）；只给一只眼睛，不解释 |
| S3 MS 50mm 固定 | 静默 0.6s 后推进；"房间没人"制造信息落差 |
| S4 CU 85mm 俯拍 | 图形匹配收尾；钥匙消失留下钩子，同时完成道具线索的 payoff |

信息释放：S1 观众知道"要开门" → S2 观众知道"门后有人" → S3 观众知道"人不在这个房间" → S4 观众知道"钥匙没了"。

## 换成你的故事

改 `characters / locations / props / shots / lines` 即可，字段别删；`lock` 写成可原样粘贴的短语，不要写"看起来像……"。
