# SeerLab 提示词包

配套文档：`Docs/SeerLab-设计.md`
用途：`原图裁切 → 图片 API 净化 → Meshy 图生 3D`

---

## 0. 通用风格锚点（每条提示词都拼上，保证 5 件像一家人）

```
Art direction (must match exactly): late-2000s Chinese sci-fi cartoon,
cream/ivory armor panels with dark gray seams and small rivets,
cyan glowing strips and glass, flat cel shading with clean dark outlines,
soft pastel highlights, no photorealism, no grunge, no gradients.
```

---

## 1. 孵化舱（Incubator pod）

### 净化提示词
```
Clean up this game prop into a 3D-model reference image. Keep ONLY one incubator pod:
a cream-and-ivory egg-shaped capsule with a large oval glass window on the front,
a small creature silhouette faintly visible inside, a dark gray circular pedestal base
with a cyan glowing ring around it, and a thin control strip below the window.
Remove the neighboring pods, the characters standing in front, all UI, text and background clutter.
Center the pod on a plain light gray background, entire object in frame,
front three-quarter view at eye level, soft even studio lighting, no cast shadow, no reflection.
[STYLE LOCK]
```

### 背面补图（孵化舱背后有管线接口，值得补）
```
Same incubator pod from the back: cream armor shell, dark gray seams,
two thick cable ports at the lower back, a small vent grille.
Orthographic back view, plain light gray background, same lighting and style.
[STYLE LOCK]
```

---

## 2. 传送台水晶（Floating crystal）

### 净化提示词
```
Clean up this game prop into a 3D-model reference image. Keep ONLY the floating crystal:
a translucent pale-cyan faceted crystal, roughly a double-terminated quartz shape,
slightly irregular, with a bright inner glow.
Remove the circular platform, the light beam, the two canisters, the characters, all UI and text.
Center the crystal on a plain light gray background, entire object in frame,
front view at eye level, soft even lighting, no cast shadow.
[STYLE LOCK]
```

> 台座不要跟着水晶一起生成——台座是 `A6 环形地台`，Blender 参数化做，尺寸才准。

---

## 3. 弧形控制设备（Arc console, 西墙）

### 净化提示词
```
Clean up this game prop into a 3D-model reference image. Keep ONLY the large curved console:
a semicircular cream-armored workstation, a big round porthole window with pale cyan glass,
a glowing cyan ring around the porthole, a dark navy screen panel on the front face,
small vents, rivets and panel seams along the body.
Remove the flat panel behind it, the characters, all UI, text and background clutter.
Center the console on a plain light gray background, entire object in frame,
front three-quarter view at eye level, soft even studio lighting, no cast shadow.
[STYLE LOCK]
```

---

## 4. 气瓶组 + 小反应器（Gas canisters）

### 净化提示词
```
Clean up this game prop into a 3D-model reference image. Keep ONLY these three objects as one group:
a tall brass-gold gas cylinder with dark banding and a domed cap,
a dark blue-gray gas cylinder with a round pressure gauge on top,
and a small round reactor on a short pedestal with a bronze ring and a glowing core.
Remove the platform base, the characters, all UI, text and background clutter.
Center the group on a plain light gray background, all objects fully in frame,
front three-quarter view at eye level, soft even studio lighting, no cast shadow.
[STYLE LOCK]
```

> 三个物件建议**分开生成三次**，在 Unreal 里再摆位置；合成生成容易粘连。

---

## 5. 工作台 + 齿轮机构（Workbench）

### 净化提示词
```
Clean up this game prop into a 3D-model reference image. Keep ONLY the rectangular workbench:
a cream-framed table with a glowing cyan rectangular window inset in the top surface,
dark gray trim and a low ribbed base.
Remove the gear hatch next to it, the characters, all UI, text and background clutter.
Center the workbench on a plain light gray background, entire object in frame,
front three-quarter view at eye level, soft even studio lighting, no cast shadow.
[STYLE LOCK]
```

### 齿轮门补图（单独一件）
```
Same style: a heavy rectangular hatch door set in a wall, dark gray metal,
a large circular gear ring on the face, a horizontal cyan glowing slot,
cream armor trim around the frame.
Front view, plain light gray background, soft even lighting, no cast shadow.
[STYLE LOCK]
```

---

## 6. 负向提示词（种子/即梦、SD、可灵等支持 negative 的接口）

```
characters, robot, mascot, text, watermark, logo, UI, HUD, buttons, icons,
multiple different objects, duplicates, perspective distortion, fisheye,
photorealistic, realistic brushed metal, dirt, scratches, noise, blur,
extra limbs, floating debris, drop shadow, floor plane, background scenery
```

> gpt-image 系列没有 negative_prompt 参数，把上面这些用 "no ..." 写进正文即可。

---

## 7. 中文版（即梦 / 通义万相 / Seedream 直接用）

**风格锚点**
```
纯正 2000 年代末中国科幻卡通风：米白装甲板、深灰接缝与铆钉、青色发光条与玻璃、
平涂赛璐璐上色、干净的深色描边、柔和高光，不要写实、不要脏旧、不要渐变。
```

**物体描述（一行一个，拼在风格锚点后面）**
- 孵化舱：米白蛋形孵化舱，正面大椭圆玻璃窗，窗内隐约一只小精灵剪影，深灰圆形底座带青色发光环，窗体下方一条细控制灯带
- 水晶：悬浮的浅青色多面晶体，双端尖、形状略不规则，内部有明亮辉光
- 弧形控制设备：半圆形米白装甲控制台，正面大圆形舷窗透出浅青光，舷窗外圈一圈青色发光环，正面下半部一块深蓝屏幕，机身有散热口和铆钉
- 气瓶组：一只高个黄铜色气瓶带深色环箍和圆顶盖，一只深蓝灰气瓶顶部带圆形压力表，一台小型圆形反应器带青铜环和发光核心
- 工作台：米白框架长方工作台，台面内嵌一块青蓝色发光矩形窗，深灰包边，底部带矮肋状基座

**通用补充**
```
单件物体、正面四分之三视角、平视、物体完整居中、浅灰纯色背景、均匀柔光、
无投影、无文字、无 UI、无角色
```

---

## 8. 生成参数

| 项 | 建议 |
|---|---|
| 尺寸 | 1024×1024（gpt-image 固定 1024×1024 / 1024×1536 / 1536×1024） |
| 质量 | `high`（每件多花几美分，但边缘和接缝清楚很多） |
| 背景 | 浅灰纯色 `#D8D8D8`，不要透明——3D 生成对 alpha 边缘处理不好 |
| 每件张数 | 先出 4 张挑 1 张；挑中的那张再跑一次同样提示词做"细化" |
| 参考一致性 | 把第 2 件的成品当作 reference image 传给第 3 件，比纯文字更稳 |

---

## 9. Meshy 图生 3D 参数

| 项 | 取值 | 原因 |
|---|---|---|
| 模式 | Image to 3D | — |
| AI Model | 最新（meshy-6 或更高） | 硬表面细节保留更好 |
| Topology | Triangle | 后面在 Blender 里减面 |
| 目标面数 | 10k–15k | 够细节，又不拖累 UE |
| Symmetry | 关 | 只有孵化舱可开，其余不对称 |
| Texture | 开 | 只作参考，进 UE 后我们重做材质 |
| 单次生成 | 1 件 1 次 | `generate_3d` 不允许一次多件 |

**重要**：我们最终用的是 Meshy 的**形状**，不是它的贴图。材质在 UE 里按设计文档的配色重做，否则卡通感会被 Meshy 的 PBR 写实贴图毁掉。
