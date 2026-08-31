# Old Sword Blocking

A small client side visual mod for **Minecraft 1.21.11**, **Fabric**.

It started as one thing — bringing back the pre-1.9 sword block — and has grown a few more
cosmetics that live in the same place. Everything here is **visual only and client side**: no
packets are added or changed, the server is never told anything, no gameplay value moves, and
nobody else sees any of it. Only the person using it needs it installed.

<img src="docs/pose-normal.png" alt="Sword held normally, with the HUD" width="410">
<img src="docs/pose-blocking.png" alt="Sword raised in the old block stance" width="410">

<img src="docs/sword-trail.png" alt="A diamond sword's streak" width="410">
<img src="docs/trail-golden.png" alt="A golden sword's streak" width="410">

<img src="docs/pose-third-person.png" alt="The block arm pose in third person" width="410">

Every shot comes straight out of the automated client test described at the bottom.

## What it does

### The 1.8 sword block

Hold right click with a sword and the sword goes up, the way it did before 1.9. Your own body
raises the arm in F5 too.

The pose is not invented. Vanilla still carries it: an item whose `UseAction` is `BLOCK` and which
is not a shield gets exactly that transform in `HeldItemRenderer` — the modern descendant of 1.8's
`ItemRenderer#doBlockTransformations`. Swords simply never reach that branch any more, because
since 1.9 right clicking a sword does nothing at all. So the mod takes the branch for them.

Be clear about the limit, because it matters in PvP: you take **exactly the same damage**. There is
no 50% reduction, no knockback change, no hit cancelling. Real blocking needs a server side mod
that every player installs — a different project.

The pose is suppressed whenever right click means something else, so it never lies to you:

| Situation | Pose |
|---|---|
| Sword in main hand, nothing else happening | shown |
| Any screen open (chest, chat, inventory), window unfocused | hidden |
| Eating, drawing a bow, raising a shield, using a spyglass | hidden |
| Placing a block from the off hand at a block you are looking at | hidden |
| Spectator | hidden |

### Weighted swing

Every blade now swings like itself. A golden sword flicks out and snaps back; a netherite one winds
up, falls through a wider arc and settles at the end. Tridents and maces are heavier still.

This is vanilla's own swing re-parameterised, not replaced — the same translation and the same
three rotations, with three knobs on top: how much the blade has to be hauled around (which warps
the timing), how far the arm travels, and how much it rocks back as it lands. **The swing still
lasts exactly as long as vanilla's**, because its length is the attack animation the server drives.
Only the shape of the motion inside those ticks changes, so nothing about reach or attack speed
moves.

<img src="docs/swing-arcs.svg" alt="Blade tip paths for each material" width="620">

That is measured, not drawn by hand: `tools/SwingProbe.java` runs the real transform outside the
game and prints the blade tip's path. Reach grows with weight (golden 1.32 → mace 1.73 blocks), the
moment the blade is furthest through the swing slides later (golden at 32% of the swing, mace at
54%), and every profile returns exactly to rest at the end.

`swing.strength` blends the whole thing back toward vanilla, `swing.perMaterial` turns off the
per-material table, and `swing.weight` and `swing.arc` scale the two halves of the effect.

### Trident and arrow streaks, and where they landed

<img src="docs/projectile-trail.png" alt="A thrown trident with its streak" width="410">
<img src="docs/landing-marks.png" alt="Marks over a landed arrow and trident" width="410">

A trident or an arrow in flight drags the same kind of streak the sword does — cyan for a trident,
pale for an arrow, and a tipped arrow streaks in its own potion colour. Because a projectile is a
point rather than a blade, each frame's two edges are made by stepping sideways from the flight
path, square to the line from the camera, so the ribbon faces you whatever angle the shot crosses
at.

Where one comes down, it leaves a mark: an exclamation mark above the spot, amber for an arrow and
cyan for a trident, **drawn through walls** so you can walk to it. The mark grows with distance to
keep roughly the same size on screen — a fixed size is fine for a nameplate a few blocks away and
invisible for a shot that went forty.

A mark is taken away when you get close, when the thing is no longer at that spot — picked up, or
broken — or when its lifetime runs out. "No longer there" is only concluded within 32 blocks, since
past that the projectile is not loaded on your client and its absence means nothing.

### Swing trail

The blade drags a glowing streak behind it as you swing. Each rendered frame the hilt and tip of
the blade are recorded, and the streak is the ribbon stitched between those frames — narrowing and
fading into its tail, soft at the edges rather than a flat band.

**Every sword material gets its own streak.** Wood is a dull warm brown, gold a bright amber,
diamond cyan, netherite a pale violet, and so on. Tridents and maces have their own too. Colours
are picked to read against the world rather than to match the item exactly: netherite's real near
black would be invisible as a trail, so it gets the sheen the item has in bright light instead.

| Material | Streak |
|---|---|
| wooden | `#C79155` |
| stone | `#BFBFBF` |
| copper | `#E8874F` |
| iron | `#E9EEF5` |
| golden | `#FFD84D` |
| diamond | `#7FF3E4` |
| netherite | `#C0A8C8` |
| trident | `#4FD8CF` |
| mace | `#9A87C4` |

Anything unrecognised — a modded sword — falls back to `trail.color`, and can be given its own
colour with `trail.colorsByItem`. Set `trail.colorPerMaterial` to `false` for one colour throughout.

The streak follows a vanilla sword's blade exactly, because its two ends are placed where the
`item/handheld` first person display transform actually puts them. Both endpoints, opacity and
length are in the config, so a resource pack with unusual sword models can be dialled in by hand.

### FPS and ping

One compact line — `45 fps · 18 ms` — with each number coloured by how healthy it is and the units
dimmed, so the eye lands on the digits. Hidden automatically while the F3 screen is up, since that
already says both, and while any screen is open.

### Gear durability, with a warning

A column in the bottom right corner: the durability **actually left** on each piece of armour and
each held tool, next to its icon, coloured by how much of it there is. Points left, not a
percentage — that is the number you act on.

Anything that drops into the danger zone gets a pulsing red badge in the corner of its icon, starts
**shaking in short bursts**, and gets **one** line in chat naming the piece — so a helmet never
quietly pops mid fight. The closer to breaking, the harder and the more often it shakes, and each
piece runs on its own clock so a row of them does not judder in lockstep. Only the icon moves; the
number beside it stays put and stays readable. A repair or a swap arms the warning again.

Both widgets sit bare on the screen by default. `hud.background` puts a soft panel behind them,
`hud.gearLayout` switches the column back to a row, and every corner is a `hud.*Anchor` away.

## Install

1. [Fabric Loader](https://fabricmc.net/use/installer/) 0.19.3 or newer, for Minecraft 1.21.11.
2. [Fabric API](https://modrinth.com/mod/fabric-api) for 1.21.11 into `mods/`.
3. **[dist/old-sword-blocking-1.6.0.jar](dist/old-sword-blocking-1.6.0.jar)** into `mods/`
   (use the *Download raw file* button on GitHub).

Java 21 or newer, same as 1.21.11 itself.

## Controls

- **Keybind** — *Options → Controls → Gameplay → Toggle sword blocking*. Unbound by default so it
  cannot collide with a key you already use. It toggles the block pose, not the HUD.
- **Commands** — `/oldswordblock status`, `/oldswordblock toggle`, `/oldswordblock reload`.
  These are client commands: they never reach the server.

## Config

`config/old-sword-blocking.json`, written on first launch. `/oldswordblock reload` re-reads it
without restarting the game.

### Block pose

| Key | Default | What it does |
|---|---|---|
| `enabled` | `true` | Master switch for the whole mod |
| `firstPerson` | `true` | The pose on your own hand |
| `thirdPerson` | `true` | Your own body in F5 raises the arm too |
| `allowSwords` | `true` | Everything in the `minecraft:swords` tag, modded swords included |
| `allowAxes` | `false` | Same for `minecraft:axes` |
| `allowAnyItem` | `false` | Block with literally anything |
| `extraItems` | `[]` | Extra ids, e.g. `["minecraft:trident"]` |
| `requireEmptyOffhand` | `false` | Closest to 1.8, which had no off hand at all |
| `suppressWhenPlacingFromOffhand` | `true` | Do not pose while right click is stacking blocks |
| `allowWhileSwinging` | `true` | 1.8 swung the blocked sword too. `false` drops the pose for the duration of a swing |
| `transitionTicks` | `2` | Ticks to ease in and out. `0` snaps instantly, like 1.8 |
| `offsetX/Y/Z`, `rotationX/Y/Z`, `scale` | 1.8 values | Pose tuning, see below |

Those pose defaults are Minecraft's own numbers for a non-shield item with `UseAction.BLOCK`.
`offsetX`, `rotationY` and `rotationZ` are mirrored automatically if you play left handed.

### `trail`

| Key | Default | What it does |
|---|---|---|
| `enabled` | `true` | |
| `samples` | `16` | How many rendered frames the streak spans |
| `color` | `#8AE9FF` | Fallback for anything the material table does not know |
| `colorPerMaterial` | `true` | Give each sword material its own streak colour |
| `colorsByItem` | `{}` | Per item overrides, e.g. `{"somemod:katana": "#FF4D6D"}` |
| `opacity` | `0.85` | Opacity at the blade end; the tail always fades to nothing |
| `smoothing` | `3` | Points inserted between frames, so a fast swing curves instead of faceting |
| `nearX/Y/Z`, `farX/Y/Z` | blade ends | Where the streak sits, in hand space. Mirrored for left handers |

The streak uses the same item rules as the block pose, so whatever you can block with is what
leaves a streak.

### `swing`

| Key | Default | What it does |
|---|---|---|
| `enabled` | `true` | |
| `perMaterial` | `true` | Each material its own weight and arc |
| `strength` | `1.0` | `0` is vanilla's swing untouched, `1` the full effect |
| `weight` | `1.0` | Multiplies how much heavier blades wind up |
| `arc` | `1.0` | Multiplies how far the arm travels |

### `projectiles`

| Key | Default | What it does |
|---|---|---|
| `trail` | `true` | The streak behind a projectile in flight |
| `trailArrows`, `trailTridents` | `true` | |
| `width` | `0.09` | Half width of the streak, in blocks |
| `samples` | `16` | How many frames the streak spans |
| `opacity` | `0.75` | |
| `smoothing` | `2` | |
| `usePotionColor` | `true` | Tipped arrows streak in their potion's colour |
| `markers` | `true` | The mark left where a projectile lands |
| `markArrows`, `markTridents` | `true` | |
| `onlyMine` | `true` | Only mark projectiles you fired yourself |
| `maxMarkers` | `12` | Oldest marks drop off past this |
| `lifetimeSeconds` | `240` | |
| `clearWithinBlocks` | `3.0` | Drop the mark once you are this close |
| `markerScale` | `1.0` | |

### `hud`

| Key | Default | What it does |
|---|---|---|
| `background` | `false` | A soft panel behind each widget |
| `outlineText` | `true` | Ring the text in dark rather than dropping one shadow |
| `scale` | `1.0` | Size of the whole HUD. Worth raising on a phone |
| `showFps`, `showPing` | `true` | |
| `infoAnchor` | `TOP_LEFT` | `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT` or `BOTTOM_RIGHT` |
| `infoOffsetX/Y` | `4` | Pixels inwards from that corner |
| `showGear` | `true` | The armour and tool column |
| `gearAnchor` | `BOTTOM_RIGHT` | |
| `gearOffsetX` | `4` | |
| `gearOffsetY` | `4` | |
| `gearLayout` | `VERTICAL` | `VERTICAL` down the side, or `HORIZONTAL` in a row |
| `onlyDamagedGear` | `false` | Hide pieces still at full durability |
| `showDurabilityNumbers` | `true` | The durability left, as a number, beside each icon |
| `showMaxDurability` | `false` | Show the maximum too, as `312/363` |
| `showBar` | `false` | The small durability bar. Redundant once the numbers are on |
| `includeOffHand` | `true` | |
| `warnBelowPercent` | `15` | At or below this, a piece gets the exclamation mark |
| `warnInChat` | `true` | The one off chat line naming the piece |
| `shakeWhenLow` | `true` | Shake a nearly broken piece, in bursts, harder the closer it gets |

## How it works

Two mixins and two HUD elements, all client only:

- `HeldItemRendererMixin` — at the head of `renderFirstPersonItem`: feeds the blade's position to
  the trail, then, when the mod says you are blocking, applies vanilla's own equip offset and
  swing, then the old block transform, and hands the stack straight back to vanilla's item
  renderer. Nothing about how the item is drawn is reimplemented.
- `PlayerEntityRendererMixin` — turns your own `ArmPose.ITEM` into `ArmPose.BLOCK` in third person,
  and only ever for the local player, so other people's models are untouched.
- `InfoHud` and `GearHud` — registered through Fabric's `HudElementRegistry`, drawing after the
  vanilla HUD.
- `ProjectileTrails` and `LandingMarkers` — drawn in the world pass through
  `WorldRenderEvents.AFTER_ENTITIES`, and the marks are geometry rather than a font glyph so they
  stay crisp at any distance.

The "am I blocking" decision lives in `BlockingState` and reads exactly one thing from the game:
whether the use key is held. It writes nothing back.

## Build from source

```
cd old-sword-blocking
./gradlew build
```

The jar lands in `build/libs/`. `./gradlew runClient` launches a dev client with the mod loaded.

There is also a real client test:

```
./gradlew runGametestClient
```

It boots an actual game, creates a creative world, hands the player a battered set of armour and a
sword, holds the use key, swings, and asserts that the mod enters and leaves the block state and
that a swing actually produces trail geometry — including that an empty hand never poses.
Screenshots of each stage land in `run/screenshots/`; the ones in `docs/` came from a run of it.

Built and verified against Minecraft 1.21.11, Yarn 1.21.11+build.6, Loader 0.19.3,
Fabric API 0.141.6+1.21.11, Loom 1.17.20, Gradle 9.5.

## Notes

**Black squares where items should be.** Since 1.21.9 every item drawn in a frame takes a slot in a
GPU atlas whose size is capped by your device's maximum texture size. A full creative tab can fill
that atlas on its own where that cap is small — some Android launchers and GL translation layers
sit well below a desktop GPU — and whatever does not fit renders as a black square. The gear strip
therefore draws nothing at all while a screen is open, so it never spends those slots at the worst
possible moment. If you still see black squares with the strip hidden, the cap is the cause and
nothing in this mod can raise it: lowering the **GUI Scale** shrinks every atlas cell and fits far
more items.

## Compatibility

Anything else that mixes into `HeldItemRenderer#renderFirstPersonItem` at head and cancels
(some animation and "old animations" mods do) can conflict — whichever cancels first wins. If your
sword pose stops appearing after adding such a mod, that is the cause.

The mod id stays `oldswordblocking` even though it now does more than blocking, so existing
configs keep working.

## Licence

MIT, same as the rest of this repository.
