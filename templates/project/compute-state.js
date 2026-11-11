// 通用纯函数时间轴：state = f(t)。任何 seek / 逐帧 / 重播都从这里重建，不累积状态。
// 依赖：story.js 由 tools/build_timeline.py 生成。
import * as THREE from 'three';
import { STORY } from './story.js';

const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const smooth = (x) => { const t = clamp(x, 0, 1); return t * t * (3 - 2 * t); };

/** 曲线采样：数值线性插值；颜色返回 THREE.Color；支持 0.2s 硬切（关键点相邻即可）。 */
export function sampleCurve(points, t) {
  if (!points || !points.length) return 0;
  if (t <= points[0][0]) return points[0][1];
  for (let i = 0; i < points.length - 1; i++) {
    const [t0, v0] = points[i];
    const [t1, v1] = points[i + 1];
    if (t <= t1) {
      const u = t1 === t0 ? 0 : (t - t0) / (t1 - t0);
      if (typeof v0 === 'string') return new THREE.Color(v0).lerp(new THREE.Color(v1), u);
      return v0 + (v1 - v0) * u;
    }
  }
  return points[points.length - 1][1];
}

/** 当前镜头（半开区间 [start, end)）；最后一段时间归入末镜。 */
export function findShot(t) {
  const shots = STORY.shots;
  for (const s of shots) if (t >= s.start && t < s.end) return s;
  return shots[shots.length - 1];
}

/** 相机插值：每个镜头提供 cam.p0/l0 → cam.p1/l1，按镜头内进度平滑插值。 */
export function cameraAt(t) {
  const s = findShot(t);
  const u = smooth((t - s.start) / Math.max(0.001, s.end - s.start));
  const cam = s.cam || { p0: [0, 2, 10], l0: [0, 0, 0], p1: [0, 2, 10], l1: [0, 0, 0] };
  const lerp3 = (a, b) => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u];
  return { p: lerp3(cam.p0, cam.p1), l: lerp3(cam.l0, cam.l1), shot: s, u };
}

/** 当前字幕：与音频同源，line.start/end 由实测时长生成。 */
export function lineAt(t) {
  return STORY.lines.find((l) => t >= l.start && t <= l.end) || null;
}

/** 事件状态：返回当前生效的 foley/ambience 等，以及一次性事件是否刚触发。 */
export function eventsAt(t, prevT) {
  const active = [];
  const fired = [];
  for (const e of STORY.events || []) {
    const from = e.from ?? e.t;
    const to = e.to ?? e.t;
    if (t >= from && t < to) active.push(e);
    if (prevT != null && prevT < e.t && t >= e.t) fired.push(e);
  }
  return { active, fired };
}

/** 总状态：世界/UI/音频都只读这个对象。 */
export function computeState(t, prevT = null) {
  const s = { t };
  for (const [k, pts] of Object.entries(STORY.curves || {})) s[k] = sampleCurve(pts, t);

  const { p, l, shot, u } = cameraAt(t);
  s.shot = shot;
  s.shotProgress = u;
  s.camPos = p;
  s.camLook = l;
  s.fade = shot.fade ? clamp(1 - (t - shot.start) / shot.fade, 0, 1) : 0;
  s.line = lineAt(t);
  s.events = eventsAt(t, prevT);
  s.finished = t >= STORY.meta.duration;
  return s;
}

export const TOTAL = STORY.meta.duration;
export const FPS = STORY.meta.fps;
