# 逼真 3D 场景：材质、光照、大气、后期

> 目标：让画面经得起 1080p 特写，而不是"低多边形风格化"。
> 铁律：**真实感 70% 来自光照与材质，20% 来自后期，10% 来自模型面数。**

## 1. 色彩科学（先做这个，否则后面全白干）

```js
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;   // 或 AgX
renderer.toneMappingExposure = 1.0;                   // 全片固定，不逐镜改
```

- 全流程线性工作：`THREE.Color` 存线性值，贴图区分 sRGB（basecolor/emissive）与 Linear（normal/roughness/AO）。
- 自定义 ShaderMaterial 末尾必须走统一管线：

```glsl
gl_FragColor = vec4(color, 1.0);
#include <tonemapping_fragment>
#include <colorspace_fragment>
```

- 后期用 `postprocessing` 时：`renderer.toneMapping = NoToneMapping`，把 `ToneMappingEffect` 放管线末端，中间缓冲用 `HalfFloatType` 防 banding。
- 全片一支 LUT，所有镜头共用；曝光/白平衡固定。

## 2. 材质（PBR）

```js
new THREE.MeshPhysicalMaterial({
  color, map, normalMap, roughnessMap, metalnessMap, aoMap,
  metalness: 0.0, roughness: 0.8,
  clearcoat: 0.0, clearcoatRoughness: 0.1,   // 漆面/湿面
  sheen: 0.0,                                 // 布料
  transmission: 0.0, thickness: 0.0, ior: 1.31, // 冰/玻璃
  envMapIntensity: 1.0,
});
```

| 表面 | metalness | roughness | 备注 |
|---|---|---|---|
| 船体漆面 | 0.0–0.1 | 0.55–0.75 | 加 clearcoat 0.2 做湿感 |
| 裸金属/锈 | 0.6–0.9 | 0.45–0.8 | 锈处 metalness 降低、roughness 升高 |
| 冰 | 0.0 | 0.05–0.2 | transmission 0.6–0.95，thickness 按体积 |
| 海水 | 0.0 | 0.05–0.15 | 靠法线+反射，不靠 metalness |
| 布料（制服） | 0.0 | 0.85–0.95 | sheen 0.2 提布感 |
| 皮肤 | 0.0 | 0.45–0.6 | 需要 subsurface（three 用 `MeshPhysicalMaterial` + 自定义 SSS 或贴图近似） |

> 非海洋题材按"同类表面"映射：船体漆面 → 建筑/机械外壳；海水 → 任何液体表面；冰 → 玻璃/晶体/透明材质。参数逻辑不变。

**细节三件套**：basecolor（色）+ normal（形）+ roughness（光）。缺任一都会"塑料"。

**纹素密度**：统一按 `px/m` 计算，同场景偏差 ≤20%。程序化几何没有好 UV 时用 triplanar 投影。

**风化**：曲率遮罩（边缘/接缝）+ 世界高度（水线）+ 噪声（斑块）。锈只长在接缝、铆钉、水线以上 1m。

## 3. 光照（真实感的主战场）

### 3.1 三层结构

1. **环境层（IBL）**：HDRI + PMREM。
```js
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromEquirectangular(hdrTex).texture;
scene.environmentIntensity = 0.6;   // 夜景 0.3–0.5
scene.background = hdrTex;          // 或单独的渐变天空
```
2. **主光（key）**：方向光/聚光，定义明暗关系与阴影方向。
3. **实用光（practical）**：画面内可见光源（舷灯、仪表、探照灯、应急灯），负责"动机"。

### 3.2 阴影

```js
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;   // 或 VSM
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.near = 1; key.shadow.camera.far = 200;
key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02;
```
- 自定义 ShaderMaterial 不接收阴影，需要接 `shadowmap_pars_fragment` 等 chunk，或改用 `MeshStandardMaterial`。
- 接触阴影：小范围、高分辨率的方向光阴影，或屏幕空间 AO。

### 3.3 环境光遮蔽与反射

- **SSAO/GTAO**：`N8python/n8ao`（时间稳定）或 `postprocessing` 的 `SSAOEffect`。
- **SSR**：屏幕空间反射，用于湿甲板、水面、金属。
- **光照探针/烘焙**：静态场景可烘 lightmap，动态物体用探针。

### 3.4 体积与大气

- **高度雾**：`fogFactor = 1 - exp(-density * dist)`，密度随高度衰减；近处清、远处沉。
- **体积光**：聚光灯锥体 + 噪声 + 深度衰减；或 raymarch（成本高）。
- **God rays**：屏幕空间径向模糊，需光源遮挡图。
- **云**：raymarched 体积云（成本高）或天空盒 + 视差层。

## 4. 水体（本类题材的核心）

- 几何：Gerstner 波（4–6 组），顶点位移 + 解析法线。
- 材质：低 roughness + 环境反射 + 菲涅尔；深处加一点次表面散射（青绿）。
- 泡沫：波峰高度阈值 + 噪声 + 时间演化，白色叠加。
- 交互：船体周围的尾迹（拉长噪声 + 距离衰减）、浪花粒子。
- 水下：折射 + 吸收（Beer-Lambert），颜色随深度变化。

## 5. 后期

| 效果 | 参数 | 作用 |
|---|---|---|
| Bloom | intensity 0.2–0.5, threshold 0.8 | 灯光/高光溢出 |
| DOF | focusDistance 跟主体, bokehScale 2–4 | 电影感、引导注意 |
| LUT | 一支冷灰/青橙 3D LUT | 统一色调 |
| 色差 | 0.0005–0.002 | 镜头缺陷 |
| 颗粒 | 0.03–0.08 | 掩盖 banding、胶片感 |
| 暗角 | 0.3–0.6 | 压边、聚焦 |
| 运动模糊 | 速度缓冲 | 高速运动 |
| TAA/SMAA | — | 抗锯齿；TAA 需速度缓冲 |

**顺序**：AO → 反射 → Bloom → 色调映射 → 抗锯齿 → 颗粒/暗角。
**集显降级**：关 SSAO → 关 DOF → 降 DPR → 降分辨率（Bloom 最后砍）。

## 6. 性能与资产

- LOD：近/中/远三档，远景用 impostor。
- Instancing：箱体、人群、粒子、植被。
- 合批：同材质合并；材质数 ≤40。
- 纹理：KTX2 + mipmap + 各向异性 4–8；纹理内存 ≤512MB（桌面）/≤64MB（集显）。
- 预算（1080p 桌面）：三角面 ≤2M、draw call ≤300、后期 ≤4 pass。
- 预算（1280×720 集显）：三角面 ≤300k、draw call ≤120、后期 ≤3 pass。

## 7. 场景验收

- [ ] 特写 1m 内可见 ≥3 层材质细节（色/法线/粗糙度）
- [ ] 无过曝（高光有细节）与死黑（暗部有层次）
- [ ] 阴影方向全片一致，接触处不"飘"
- [ ] 同场景纹素密度偏差 ≤20%
- [ ] 雾不遮蔽主体（主体与背景至少有 15% 亮度差）
- [ ] 水面有反射与泡沫，船体有尾迹
- [ ] 全片同一 LUT、同一曝光

## 8. 多尺度细节契约（来自 ohmygame threejs-world）

真实感不是"面数多"，而是**三个尺度都成立**：

| 尺度 | 要求 | 检查 |
|---|---|---|
| **世界尺度** | 边界、区域关系、入口、路线、整体构图可读；前景/中景/背景有纵深；负空间是有意留的 | 总览截图能否一眼说出"这是哪、往哪走" |
| **中尺度** | 建筑/地标/主体有可辨识的剪影、比例、构造与连接关系 | 主角特写能否看出"它是什么做的" |
| **近距离** | 材质差异、表面变化、接缝、与环境相符的磨损、局部构件、活动痕迹 | 1m 特写能否看到 ≥3 层细节 |

**细节分布**：细节要**集中在有人活动的区域和主角附近**，远处保持安静；均匀撒细节、整齐复制细节，都不算丰富。

**视觉统一**：光、材质、阴影、雾、颜色、运动要协同表达同一主题，并承担"揭示体积、引导注意力"的职责。

**审查视图**（每次改完都要重截）：总览 / 主路线 / 主角特写 / 环境细节特写 / 窄视口（手机）。

**不合格信号**：用 box/cylinder 顶着主体的名字；默认材质；只靠对象名和对象数量宣称完成；只给一张远景。
