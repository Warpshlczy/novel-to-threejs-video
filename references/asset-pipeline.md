# 资产管线：从来源到进引擎

> 目标：让"摄影级资产"进得来、装得下、对得齐、不穿帮。
> 顺序：**等级与预算 → 来源 → 生成 → 重拓扑/UV → 纹理 → 绑定/动画 → 规范化 → 压缩 → 台账 → 验收**。

## 1. 等级与预算（先做这一步）

| 等级 | 判定标准 | 角色 | 场景/道具 | 允许画幅 |
|---|---|---|---|---|
| T0 | 占位几何 | 胶囊/球/柱 | 灰盒 | 禁止进成片 |
| T1 | 有造型、无细节 | CC0 低模、风格化 VRM、≤15k 三角面 | CC0 模块、≤10k | ≤ MS |
| T2 | 有 PBR、有绑定 | 人形骨骼 ≥30、2K 贴图、≤60k | 2K PBR、倒角、≤30k | ≤ MCU |
| T3 | 有皮肤细节、有表情 | 骨骼 ≥55、blendshape ≥15、4K 皮肤、≤120k | 4K PBR + decal + wear | 不限 |

**预算分配（典型 90s 单集）**

| 项 | 数量 | 说明 |
|---|---|---|
| T3 角色 | 1–2 | 只给有 CU/ECU 的角色 |
| T2 角色 | 1–4 | 对话、群像主位 |
| T1 角色 | 5–30 | 背景、剪影、远景 |
| T3 场景 | 0–1 | 只在主场景的核心角落（1m 内可见区） |
| T2 场景 | 2–4 | 主场景全身 |
| T2/T1 道具 | 3–10 | 只给被镜头"看"的 |

> 省钱原则：**T3 只买"镜头会停下来看"的东西**。90s 片子里通常只有 2–5 个这样的镜头。

## 2. 来源矩阵

### 2.1 免费 / CC0 资产库

| 来源 | 内容 | 许可 | 适合等级 | 备注 |
|---|---|---|---|---|
| Poly Haven | HDRI / PBR 贴图 / 模型 | CC0 | T2 场景、纹理 | 4K 贴图全套；API 可用 |
| ambientCG | PBR 贴图 | CC0 | T2 | 材质种类多，含 4K/8K |
| Kenney | 低模套件 | CC0 | T1 | 风格化、原型 |
| Quaternius | 低模角色/道具 | CC0 | T1 | 有动画版本 |
| KayKit | 低模套件 | CC0 | T1 | 风格化 |
| Poly Pizza | 聚合 CC0/CC-BY | 混合 | T1 | 逐件核对许可 |
| Sketchfab（CC0 筛选） | 中高模 | CC0 | T2/T3 | 检查面数与 UV |
| Smithsonian / NASA / NIH 3D | 文物/航天/生物 | 多为 CC0/公有领域 | T2/T3 道具 | 尺度与朝向常错 |
| Mixamo | 人形骨骼 + 动作库 | Adobe 条款 | 绑定/动画 | 免费，但禁止转售动画本身 |
| Rokoko / CMU Mocap | 动作捕捉 | 免费/学术 | 动画 | 需重定向 |

### 2.2 生成式（图 → 3D）

| 工具 | 能力 | 显存 | 许可 | 适合 |
|---|---|---:|---|---|
| `microsoft/TRELLIS.2` | 图生 3D，1536³，PBR，直出 GLB | 24GB | MIT | T3 首选（开源） |
| `Tencent-Hunyuan/Hunyuan3D-2.1` | 图生 3D + PBR 贴图（albedo/metallic/roughness） | 10GB 形状 / 21GB 纹理 / 29GB 全量 | 腾讯社区许可 | T3 生产（商用需核对地域/规模条款） |
| `VAST-AI-Research/TripoSG` | 高保真几何 | 8–16GB | MIT | 几何强，纹理另做 |
| `VAST-AI-Research/TripoSR` | 快速图生 3D | 6–8GB | MIT | T1/T2 背景道具 |
| `aigc3d/LAM` | 单图 → 可动高斯人头 | 12GB+ | Apache 2.0 | 只适合头部特写 |

**托管替代（无 GPU）**：`fal.ai` 有 `fal-ai/trellis-2`、`fal-ai/hunyuan-3d/*`、`fal-ai/meshy/rigging`；`Replicate` 有对应镜像。按次付费，适合只做 2–3 个 hero 资产。

### 2.3 文本 → 参考图（图生 3D 的前置）

| 工具 | 用途 | 备注 |
|---|---|---|
| FLUX / Qwen-Image | 角色三视图（正/侧/背）、道具多角度 | 固定 seed + 同一描述词，保证跨资产一致 |
| IP-Adapter / 参考图条件 | 跨镜同一角色 | 先出"角色设定板"，再逐资产生成 |
| ControlNet（depth/normal） | 控制姿态与构图 | 需要指定姿势时用 |

**关键：图生 3D 的质量上限由输入图决定。** 先出干净的正面/3-4 视角、纯色背景、均匀光、无遮挡的图，再进 3D。不要用带背景、带手、带复杂褶皱的图。

## 3. 三条生产路线

### 路线 A：零 GPU（最快、最稳）

```text
角色：VRoid Studio / Ready Player Me → .vrm 或 .glb
     → Mixamo 自动绑定 + 动作 → 导出 GLB → three-vrm / GLTFLoader
场景：Poly Haven 模型 + ambientCG 4K 贴图
道具：Poly Haven / Kenney / Quaternius
纹理：Poly Haven 4K PBR 套图 + triplanar（无 UV 时）
```

- 优点：无显存、可复现、许可清晰。
- 上限：T2。VRM 的脸是"动漫/半写实"，不适合真实人脸 ECU。
- 一致性：同一 `.vrm` 文件全片复用，只换表情与动作。

### 路线 B：本地 GPU（质量上限最高）

```text
1. 文生图：角色三视图 / 道具多角度（FLUX、Qwen-Image）
2. 图生 3D：TRELLIS.2 或 Hunyuan3D-2.1 → GLB（含 PBR）
3. 清理：MeshLab 去非流形 / 补洞 / 去浮块
4. 重拓扑：Instant Meshes → 四边面 → Blender 细分一次
5. UV：Blender Smart UV / UDIM（角色按头/身/手分 UV 岛）
6. 纹理：Hunyuan3D-Paint 或 Paint3D 投影；Substance/Material Maker 补细节
7. 绑定：UniRig（自动骨架 + 蒙皮）→ 人工校 3–5 个关节
8. 动画：Mixamo / Rokoko 重定向到 Humanoid
9. 导出：GLB + KTX2 → glTF-Transform 压缩
```

### 路线 C：托管 API（无 GPU 但要 T3）

```text
image-to-3d(provider=fal, model=fal-ai/trellis-2)
  → 下载 GLB
  → 本地 Blender headless 重拓扑/减面（CPU 可跑）
  → rig(provider=fal, model=fal-ai/meshy/rigging)
  → 下载带动画 GLB
```

> macOS 没有 CUDA：路线 B 的推理步骤在 Mac 上不可行。要么走路线 C，要么用 ComfyUI 的 MPS（慢且兼容性有限）。

## 4. 图生 3D 的输入规范

| 项 | 要求 |
|---|---|
| 视角 | 正面或 3/4 视角；多视图用支持多图的模型 |
| 背景 | 纯色/透明，无地面阴影 |
| 光照 | 均匀、无强方向光（避免把光照烘进 albedo） |
| 姿态 | A-pose 或 T-pose（利于后续绑定） |
| 分辨率 | ≥1024²，主体占画面 70–85% |
| 遮挡 | 无；手不要挡身体，头发不要挡脸 |
| 一致性 | 同一角色的多张图用同一 seed / 同一描述词 |

**生成后必做**：检查法线朝向、尺度、UV 重叠、是否含内部面。图生 3D 的输出默认**不能直接进引擎**，必须重拓扑。

## 5. 重拓扑与 UV

```bash
# Instant Meshes（GUI 或命令行）
instant-meshes --input raw.obj --output retopo.obj --target-faces 12000 --smooth 2

# Blender headless：清理 + 减面 + 法线重算
blender -b raw.glb --python tools/blender_clean.py -- --ratio 0.35 --out clean.glb
```

| 项 | 标准 |
|---|---|
| 拓扑 | 四边面优先；角色关节处环形边 |
| 面数 | 角色 T3 ≤120k、T2 ≤60k、T1 ≤15k；道具 T2 ≤10k |
| UV | 无重叠（镜像除外）；接缝藏在内侧/背面 |
| UV 岛 | 角色 ≥4 岛（头/身/手/附件）；道具 ≥2 岛 |
| 法线 | 重算外向；硬边加 bevel 或 split |
| 尺度 | 导出前用包围盒核对真实尺寸（米） |

## 6. 纹理控制

### 6.1 纹素密度（texel density）

```text
texelDensity = textureResolution / 该 UV 岛对应的真实表面积（px/m）
```

| 资产 | 目标 px/m | 贴图 |
|---|---:|---|
| T3 角色脸 | 2048–4096 | 4K |
| T3 角色身体 | 1024 | 4K（或 2K + detail normal） |
| T2 角色 | 512–1024 | 2K |
| T2 场景（近景区） | 512–1024 | 4K |
| T1 / 远景 | 128–256 | 1K |

同场景偏差 ≤20%。做不到就加 detail normal 或换 triplanar，不要靠"再放大贴图"。

### 6.2 PBR 套图

| 贴图 | 色彩空间 | 必需 |
|---|---|---|
| baseColor | sRGB | 是 |
| normal | Linear | 是 |
| roughness | Linear | 是 |
| metalness | Linear | 金属/混合表面必需 |
| AO | Linear | 场景必需，角色可选 |
| height/displacement | Linear | 可选（视差/置换） |
| emissive | sRGB | 发光件 |

**细节三件套**：baseColor（色）+ normal（形）+ roughness（光）。缺任一都会"塑料"。

### 6.3 细节层级（让 1m 特写成立）

| 层 | 频率 | 做法 |
|---|---|---|
| 宏观 | 0.5–2m | 贴图 baseColor 大色块、磨损分区 |
| 中观 | 5–50cm | normal map、接缝、缝线、铆钉 |
| 微观 | <5cm | detail normal（平铺）、roughness 变化、污渍遮罩 |

**风化/磨损生成**：曲率（边缘）+ AO（缝隙）+ 世界高度（水线/地面）+ 噪声（斑块）。锈只长在接缝、铆钉、积水线以上。

### 6.4 无 UV / UV 太差时

- **triplanar 投影**：世界坐标三平面混合，适合场景模块、岩石、地形。见 `threejs-refinement.md`。
- **decal**：贴花、标签、编号、血迹，用 `DecalGeometry` 贴到曲面上。
- **顶点色 AO**：把 AO 烘到顶点色，省一张贴图。
- **程序化遮罩**：固定 seed 的 canvas 噪声，生成污渍/水痕。

### 6.5 纹理压缩

```bash
# KTX2 + mipmap + 各向异性
npx gltf-transform optimize in.glb out.glb --texture-compress ktx2 --texture-size 2048
```

- 主体 ≥2K；远景可 1K。
- KTX2（Basis）比 JPG/PNG 省 4–8 倍显存。
- 各向异性 4–8；mipmap 必开。

## 7. 绑定与动画

| 路线 | 工具 | 骨骼 | 适用 |
|---|---|---|---|
| VRM 自带 | VRoid / Ready Player Me | Humanoid ≥50 | 路线 A |
| 自动绑定 | `VAST-AI-Research/UniRig` | 自动骨架 + 蒙皮 | 图生 3D 输出 |
| 商业自动 | Mixamo / AccuRIG | Humanoid | 人形 GLB |
| 手工 | Blender Rigify | 自定义 | T3 hero |

**绑定验收**

- [ ] 肘/膝弯曲无塌陷、无穿插
- [ ] 手指能抓握（T3 必须 15 骨手）
- [ ] 脚底贴地（IK 或逐帧校）
- [ ] 权重无"糖纸"（单顶点受 >4 骨影响）
- [ ] 表情 blendshape ≥15（T3），至少含 blink / mouthOpen / smile / browDown

**动作**

- `mixer.setTime(t - clipStart)`，不用 `update(dt)`。
- Mixamo → Humanoid 需要重定向；`three-vrm` 有 humanoid 接口。
- 每场至少一个非循环动作；静立时叠加呼吸/重心（见 `character-performance.md`）。

## 8. 规范化（进引擎前的硬检查）

| 项 | 标准 |
|---|---|
| 尺度 | 1 unit = 1 米；角色身高 1.6–1.95 |
| 朝向 | 面向 +Z（three 约定），脚底 y=0 |
| 轴心 | 角色脚底中心；道具握点或底部中心 |
| 命名 | `chr_<id>` / `prop_<id>` / `env_<id>` / `mat_<type>_<variant>` |
| 层级 | `char_<id>_<part>`；按名字定位，不靠索引 |
| 材质 | 一个资产一套材质；同材质全片复用 |
| 碰撞 | 单独简化盒/胶囊，面数低一个量级 |

## 9. 压缩与 LOD

```bash
npx gltf-transform optimize in.glb out.glb --compress draco --texture-compress ktx2
npx gltf-transform simplify in.glb lod1.glb --ratio 0.5 --error 0.001
```

- LOD 三档：L0 100%（近）、L1 50%（中）、L2 15%（远 + impostor）。
- 切换阈值按屏幕占比：>20% L0、5–20% L1、<5% L2。
- Instancing：同屏重复物（箱体、人群、植被）。
- 合批：同材质合并；材质数 ≤40。

## 10. 资产台账与可复现

`tools/build_assets.py` 产出 `assets/manifest.json`；`tools/validate_assets.py` 校验。

```jsonc
{
  "id": "chr_lead",
  "kind": "character",
  "tier": "T3",
  "source": "generated",
  "provider": { "image": "fal-ai/flux/dev", "mesh": "fal-ai/trellis-2", "rig": "fal-ai/meshy/rigging" },
  "prompt": "…（逐字保存）",
  "seed": 12345,
  "file": "assets/models/chr_lead.glb",
  "hash": "sha256:…",
  "size": [0.42, 1.78, 0.28],
  "tris": 58214,
  "bones": 65,
  "blendshapes": 18,
  "texelDensity": 1024,
  "maps": ["baseColor", "normal", "roughness"],
  "license": "original",
  "derivedFrom": ["ref/chr_lead_front.png", "ref/chr_lead_side.png"],
  "lock": "深灰立领外套，左眉有疤，右手戴皮手套"
}
```

**可复现四要素**：固定 `seed` + 固定模型版本 + 逐字保存的 `prompt` + 产物 `hash`。构建时校验 hash，不重新生成。

**稳定 asset key**：源码只引用 `chr_lead`，不引用路径；换文件只改台账。

## 11. 许可

| 类型 | 商用 | 义务 |
|---|---|---|
| CC0 | 是 | 建议登记来源 |
| CC-BY | 是 | 必须署名 |
| MIT / Apache 2.0 | 是 | 保留版权与许可声明 |
| GPL / AGPL | 谨慎 | 分发可能触发开源义务 |
| 腾讯社区许可（Hunyuan3D） | 有条件 | 核对地域、用户规模、署名 |
| bilibili 模型许可（IndexTTS） | 有条件 | 核对商用条款 |
| Adobe Mixamo | 是 | 不得转售动画/角色本身 |
| 生成物 | 随模型 | 记录模型名 + 版本 + 许可 |

**每个资产都要有 license 字段**；`assets/CREDITS.md` 汇总。

## 12. 验收

- [ ] `validate_assets.py` error = 0
- [ ] 无 T0 资产被成片镜头引用
- [ ] CU/ECU 镜头角色均为 T3；85mm 镜头主体 ≥T2
- [ ] 主体贴图 ≥2K；角色/关键道具三件套齐全
- [ ] 尺度/朝向/轴心正确，无悬空/陷地
- [ ] 纹素密度同场景偏差 ≤20%
- [ ] 无重叠 UV 导致的贴图错位
- [ ] 绑定：肘膝不塌、手指能握、脚不滑
- [ ] LOD 切换无跳变
- [ ] 台账齐全，`hash` 与文件一致，`lock` 短语逐字进设定与分镜卡
- [ ] 许可可追溯，CC-BY 已署名
