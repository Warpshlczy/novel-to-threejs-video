# 资产管线：从来源到进引擎

> 目标：让"真实资产"进得来、装得下、对得齐、不穿帮。
> 顺序：**来源与授权 → 规范化 → 材质与贴图 → 压缩与 LOD → 进引擎 → 一致性登记**。

## 1. 来源与授权

| 类型 | 来源 | 授权 | 注意 |
|---|---|---|---|
| HDRI | Poly Haven | CC0 | 1k 够用，2k 用于主光环境 |
| PBR 贴图 | Poly Haven | CC0 | basecolor/normal/roughness/AO/displacement 全套 |
| 模型 | Poly Haven / Quaternius / Kenney | CC0 | 检查面数与 UV |
| 角色 | VRM（CC0/CC-BY）、Mixamo | 按许可 | CC-BY 需署名 |
| 残骸/机械 | Smithsonian / NASA / NIH 3D | 多为 CC0/公有领域 | 检查尺度与朝向 |
| 图生 3D | TRELLIS.2 / Hunyuan3D-2.1 | 模型许可 | 生成物需重拓扑 |

> 让 agent 直接搜资产：`sozai-search-mcp`（约 36000 个 CC0 资产，含真实尺寸）；
> 批量下载 Poly Haven：`agmmnn/polydown`。

## 2. 规范化（进引擎前的硬性检查）

| 项 | 标准 |
|---|---|
| 尺度 | 1 unit = 1 米；角色身高 1.7–1.9 |
| 朝向 | 面向 +Z（three 约定），脚底在 y=0 |
| 轴心 | 角色在脚底中心；道具在"手握点"或底部中心 |
| 命名 | `chr_shen` / `prop_mug` / `env_bridge` / `mat_hull_paint` |
| UV | 无重叠（除镜像）；纹素密度统一 |
| 材质 | 一个资产一套材质，不混用 |
| 面数 | 角色 ≤60k，道具 ≤10k，场景模块 ≤30k |

## 3. 材质与贴图

- PBR 套图：`basecolor`(sRGB) / `normal`(Linear) / `roughness`(Linear) / `ao`(Linear) / `displacement`(可选)。
- 图集（atlas）：同场景小道具合并到一张图，减少 draw call。
- 纹理压缩：KTX2（Basis）+ mipmap + 各向异性 4–8。
- 程序化补充：细节噪声、风化遮罩、水线，用 canvas 或 shader 生成，固定 seed。

## 4. 压缩与 LOD

```bash
# glTF-Transform：Draco 几何 + KTX2 纹理 + 量化
npx gltf-transform optimize in.glb out.glb --compress draco --texture-compress ktx2
# 生成 LOD 链
npx gltf-transform simplify in.glb lod1.glb --ratio 0.5 --error 0.001
```

- LOD 三档：L0（近，100%）、L1（中，50%）、L2（远，15% + impostor）。
- 切换阈值按屏幕占比（>20% L0，5–20% L1，<5% L2）。
- Instancing：同屏重复物（箱体、人群、粒子、植被）。
- 合批：同材质合并；材质数 ≤40。

## 5. 进引擎

```js
const loader = new GLTFLoader();
const gltf = await loader.loadAsync('assets/props/mug.glb');
gltf.scene.traverse((o) => {
  if (o.isMesh) {
    o.castShadow = true;
    o.receiveShadow = true;
    o.material.envMapIntensity = 1.0;
  }
});
// 只加载一次，全片复用；换机位不换模型
```

- **懒加载**：按镜预取下一镜资产，避免首帧卡顿。
- **缓存**：同一资产全片一个实例，clone 时共享几何与材质。
- **释放**：不用的镜之后可 `dispose`，但要保证重播时能重建。

## 6. 一致性登记（资产台账）

**进引擎前的规范化 5 项**（不做这一步，后面所有对齐都会错）：

1. **单位**：统一米制，1 unit = 1 m；导出前用包围盒核对真实尺寸。
2. **轴向**：glTF 是 Y-up / -Z forward；Blender 导出记得 `+Y up`。
3. **pivot**：脚底/底部中心（角色、道具）、几何中心（粒子、装饰）。
4. **层级命名**：`char_<id>_<part>`、`loc_<id>`、`prop_<id>`；后续按名字定位，不靠索引。
5. **材质**：命名 `mat_<type>_<variant>`；同一材质全片复用，禁止逐镜复制。

**稳定 asset key**：源码只引用 `prop_cup`，不引用路径；换文件只改台账，不动镜头代码。

**碰撞代理**：可见几何与碰撞几何分开；碰撞用简化盒/胶囊，永远比可见面数低一个量级。

每个资产登记：ID、来源、许可、尺度、面数、材质、纹素密度、首次出现镜、锁定短语；派生资产记 `derivedFrom`。

```jsonc
{
  "id": "prop_cup",
  "source": "procedural | polyhaven | custom",
  "license": "original | CC0 | CC-BY",
  "size": [0.09, 0.12, 0.09],
  "tris": 84,
  "material": "mat_ceramic_white",
  "texelDensity": 512,
  "firstShot": "S02",
  "lock": "白色陶瓷杯，右手持，杯口朝上，无把手"
}
```

> 这是任意道具的登记格式；换成你的道具、保持字段齐全即可。`lock` 是可原样粘贴的短语，不是描述。

**锁定短语必须逐字进《视觉设定》与分镜卡片**，任何镜不得改写。

## 7. 预算

| 项 | 桌面 1080p | 集显 720p |
|---|---|---|
| 三角面总量 | ≤2M | ≤300k |
| draw call | ≤300 | ≤120 |
| 材质数 | ≤40 | ≤24 |
| 纹理内存 | ≤512MB | ≤64MB |
| 首屏加载 | ≤8s | ≤5s |

## 8. 验收

- [ ] 所有资产尺度/朝向/轴心正确，无"悬空/陷地"
- [ ] 纹素密度同场景偏差 ≤20%
- [ ] 无重叠 UV 导致的贴图错位
- [ ] LOD 切换无跳变
- [ ] 资产台账齐全，锁定短语进文档
- [ ] 许可可追溯（CC0/CC-BY 署名）
