# Three.js 侧精修：模型进来之后还能改什么

> 前提：模型不是终点。**同一份 GLB，在引擎里还能把观感提升一档**——靠材质、细节层、接触阴影、后期和光追静帧。
> 边界：Three.js 不能把胶囊变成人，也不能无中生有造出皮肤细节。它负责"把已有资产推到它应有的上限"。

## 1. 精修优先级（按性价比排序）

| 优先 | 手段 | 观感收益 | 成本 |
|---:|---|---|---|
| 1 | 接触阴影 + AO | 物体"落地"，不再漂浮 | 低 |
| 2 | roughness 变化 + detail normal | 去掉塑料感 | 低 |
| 3 | triplanar / 无 UV 贴图 | 场景模块不再糊 | 低 |
| 4 | decal（标签/编号/污渍） | 出现"使用痕迹" | 中 |
| 5 | 皮肤 SSS 近似 | 人脸从蜡像变活人 | 中 |
| 6 | DOF + LUT + 颗粒 | 电影感 | 低 |
| 7 | 光追静帧（hero shot） | 关键帧质量跃升 | 高 |

## 2. 材质精修

### 2.1 triplanar：没有 UV 也能贴

适合场景模块、地形、岩石、图生 3D 输出（UV 常烂）。

```js
function makeTriplanar(mat, tex, scale = 0.5) {
  mat.map = tex;
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uTriScale = { value: scale };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
        varying vec3 vTriPos;
        varying vec3 vTriNormal;`)
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
        vec4 triWorld = modelMatrix * vec4(transformed, 1.0);
        vTriPos = triWorld.xyz;
        vTriNormal = normalize(mat3(modelMatrix) * objectNormal);`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
        varying vec3 vTriPos;
        varying vec3 vTriNormal;
        uniform float uTriScale;`)
      .replace('#include <map_fragment>', `
        vec3 triN = normalize(vTriNormal);
        vec3 triW = pow(abs(triN), vec3(6.0));
        triW /= (triW.x + triW.y + triW.z);
        vec4 triX = texture2D(map, vTriPos.zy * uTriScale);
        vec4 triY = texture2D(map, vTriPos.xz * uTriScale);
        vec4 triZ = texture2D(map, vTriPos.xy * uTriScale);
        diffuseColor *= triX * triW.x + triY * triW.y + triZ * triW.z;`);
  };
  mat.needsUpdate = true;
}
```

- `uTriScale` 按真实世界尺寸调（0.2–1.0）；同一场景所有模块用同一 scale，纹素密度才一致。
- 只对 baseColor 用 triplanar 时最省；normal 也可用，但权重需按切线空间校正。

### 2.2 detail normal：一张平铺贴图救所有近景

```js
const detail = new THREE.TextureLoader().load('assets/textures/detail_normal_1k.jpg');
detail.wrapS = detail.wrapT = THREE.RepeatWrapping;
detail.repeat.set(8, 8);

const mat = new THREE.MeshPhysicalMaterial({
  map, normalMap, roughnessMap, roughness: 0.85, metalness: 0.0,
  normalScale: new THREE.Vector2(1.0, 1.0),
});
mat.onBeforeCompile = (shader) => {
  shader.uniforms.uDetail = { value: detail };
  shader.uniforms.uDetailScale = { value: 8.0 };
  shader.vertexShader = shader.vertexShader
    .replace('#include <common>', '#include <common>\nvarying vec2 vDetailUv;')
    .replace('#include <uv_vertex>', '#include <uv_vertex>\nvDetailUv = uv;');
  shader.fragmentShader = shader.fragmentShader
    .replace('#include <common>', `#include <common>
      uniform sampler2D uDetail;
      uniform float uDetailScale;
      varying vec2 vDetailUv;`)
    .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
      vec3 dN = texture2D(uDetail, vDetailUv * uDetailScale).xyz * 2.0 - 1.0;
      normal = normalize(normal + dN * 0.35);`);
};
```

- 细节法线强度 0.2–0.4；太强会"砂纸感"。
- 同一场景所有表面共用一张 detail normal，repeat 不同。

### 2.3 逐顶点 AO / 曲率遮罩

把 AO 或曲率烘进顶点色，省一张贴图，还能驱动磨损：

```js
const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.8 });
// 顶点色 r = AO, g = 曲率, b = 高度归一化
mat.onBeforeCompile = (shader) => {
  shader.fragmentShader = shader.fragmentShader.replace(
    '#include <color_fragment>',
    `#include <color_fragment>
     float vAO = vColor.r;
     float vCurv = vColor.g;
     diffuseColor.rgb *= mix(0.65, 1.0, vAO);
     roughnessFactor = clamp(roughnessFactor + vCurv * 0.25, 0.05, 1.0);`
  );
};
```

用途：锈长在曲率高的边缘；积灰在 AO 低处；磨损在高点。

### 2.4 皮肤：SSS 近似

`MeshPhysicalMaterial` 的 `thickness` 只对 transmission 有效，皮肤要用"假 SSS"：

```js
const skin = new THREE.MeshPhysicalMaterial({
  map, normalMap, roughnessMap,
  roughness: 0.55, metalness: 0.0,
  sheen: 0.25, sheenRoughness: 0.75, sheenColor: new THREE.Color('#c98d7a'),
  clearcoat: 0.08, clearcoatRoughness: 0.6,
});
skin.onBeforeCompile = (shader) => {
  shader.fragmentShader = shader.fragmentShader.replace(
    '#include <emissivemap_fragment>',
    `#include <emissivemap_fragment>
     float rim = pow(1.0 - saturate(dot(normalize(vNormal), normalize(vViewPosition))), 3.0);
     totalEmissiveRadiance += vec3(0.42, 0.10, 0.08) * rim * 0.12;`
  );
};
```

- 关键在**眼窝、鼻翼、耳廓的 AO** 和**边缘红光**。
- 皮肤 roughness 不要 <0.4（会像塑料）；不要 >0.7（会像石膏）。

### 2.5 clearcoat / sheen 的使用边界

| 表面 | clearcoat | sheen |
|---|---|---|
| 上漆金属、湿地面 | 0.2–0.8 | — |
| 布料（制服、毛呢） | — | 0.2–0.4 |
| 皮肤 | 0.05–0.1 | 0.2–0.3 |
| 陶瓷、珐琅 | 0.5–0.9 | — |

## 3. 几何与细节

### 3.1 Decal：标签、编号、血迹、水痕

```js
import { DecalGeometry } from 'three/addons/geometries/DecalGeometry.js';

function addDecal(mesh, point, normal, size, texture) {
  const m = new THREE.Mesh(
    new DecalGeometry(mesh, point, new THREE.Euler(), size),
    new THREE.MeshPhysicalMaterial({
      map: texture, transparent: true, depthWrite: false,
      polygonOffset: true, polygonOffsetFactor: -4,
      roughness: 0.8, metalness: 0.0,
    })
  );
  m.renderOrder = 1;
  mesh.add(m);
}
```

- 贴花是"使用痕迹"最便宜的来源：编号、警示条、锈迹、手印。
- 贴花几何会增长，单个道具 ≤8 个；导出前可合并。

### 3.2 布尔与开洞

```js
import { Evaluator, Brush } from 'three-bvh-csg';
const ev = new Evaluator();
const result = ev.evaluate(new Brush(meshA), new Brush(meshB), 2 /* SUBTRACTION */);
```

用于窗洞、舱门、破口。注意面数增长，做完立刻减面。

### 3.3 置换与倒角

- 倒角：建模阶段做（Bevel 修改器）。Three.js 里不能事后加倒角。
- 置换：`displacementMap` 需要高细分，实时成本高；只用于 hero 静帧。
- 法线贴图是"假倒角"的廉价替代：边缘画一条亮线。

## 4. 接触阴影（最容易漏的一步）

没有接触阴影，角色永远像"贴"在地面上。

```js
// A. 方向光阴影（主力）
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.bias = -0.0005;
key.shadow.normalBias = 0.02;

// B. 接触阴影贴片（廉价、稳定）
const blob = new THREE.Mesh(
  new THREE.PlaneGeometry(1.2, 1.2),
  new THREE.MeshBasicMaterial({
    map: shadowTex, transparent: true, opacity: 0.55,
    depthWrite: false, color: 0x000000,
  })
);
blob.rotation.x = -Math.PI / 2;
blob.position.y = 0.005;
```

- 角色/道具脚下必须有接触暗部；否则再好的模型也"飘"。
- 优先级：方向光阴影 > SSAO > 贴片。

## 5. 后期（顺序不能错）

```text
AO → 反射(SSR) → Bloom → 色调映射 → DOF → 抗锯齿 → LUT → 颗粒/暗角/色差
```

| 效果 | 参数 | 作用 |
|---|---|---|
| N8AO | radius 0.5–1.5, intensity 1.0–2.0, 半分辨率 | 缝隙变暗 |
| Bloom | intensity 0.2–0.5, threshold 0.8 | 高光溢出 |
| DOF | focusDistance 跟主体, bokehScale 2–4 | 引导注意 |
| LUT | 一支，全片共用 | 统一色调 |
| 颗粒 | 0.02–0.05 | 掩盖 banding |
| SMAA/TAA | — | 抗锯齿 |

**集显降级顺序**：关 SSAO → 关 DOF → 降 DPR → 降分辨率（Bloom 最后砍）。

## 6. 性能精修

| 手段 | 收益 | 做法 |
|---|---|---|
| KTX2 | 显存 -75% | `gltf-transform --texture-compress ktx2` |
| meshopt | 几何 -50% | `--compress meshopt` |
| Instancing | draw call -90% | 同屏重复物用 `InstancedMesh` |
| 合批 | draw call 下降 | 同材质合并 |
| LOD | 三角面 -70% | 三档 + 屏幕占比切换 |
| 遮挡剔除 | 填充率 | `three-mesh-bvh` 视锥/遮挡查询 |

## 7. 光追静帧（hero shot 的作弊器）

实时画面 90 分，光追静帧 98 分。关键帧用 `three-gpu-pathtracer` 单独出图，后期替换或做海报。

```js
import { WebGLPathTracer } from 'three-gpu-pathtracer';
const tracer = new WebGLPathTracer(renderer);
tracer.setScene(scene, camera);
tracer.renderScale = 1.0;
tracer.renderSamples = 256;      // 静帧可上千
tracer.tiles.set(2, 2);
// 每帧 tracer.update(); 累积到目标样本数后读回 canvas → toDataURL
```

- 只用于静帧/海报/关键帧；不要指望实时。
- 光追前把材质换成物理正确的参数（metalness/roughness 真实值），否则光追会放大错误。

## 8. 三档画质 preset

```js
export const PRESETS = {
  preview: {
    dpr: 1.0, shadows: 1024, ao: false, dof: false,
    bloom: 0.25, samples: 0, supersample: 1,
  },
  production: {
    dpr: 1.5, shadows: 2048, ao: true, dof: false,
    bloom: 0.34, samples: 4, supersample: 1,
  },
  hero: {
    dpr: 2.0, shadows: 4096, ao: true, dof: true,
    bloom: 0.4, samples: 8, supersample: 2, pathtrace: 256,
  },
};
```

- `supersample: 2` 表示按 2× 分辨率渲染再缩回，边缘与细节立刻变干净。
- 导出 MP4 时用 `production` 或 `hero`；预览用 `preview`。

## 9. 精修验收

- [ ] 角色/道具脚下有接触阴影，不悬浮
- [ ] 1m 特写能看到 baseColor + normal + roughness 三层
- [ ] 无 UV 的表面用了 triplanar，纹素密度与有 UV 的表面一致
- [ ] 皮肤 roughness 在 0.4–0.7，边缘有轻微红光
- [ ] 关键道具至少有 1 个 decal（编号/标签/污渍）
- [ ] 后期顺序正确，全片同一 LUT / 曝光
- [ ] hero 镜头有光追静帧或 2× 超采样
- [ ] KTX2 + meshopt 已启用，纹理内存达标
