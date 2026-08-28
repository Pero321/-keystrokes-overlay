# Old Sword Blocking

Hold right click with a sword and the sword goes up, the way it did before 1.9.

Minecraft **1.21.11**, **Fabric**, **client side only**.

<img src="docs/pose-normal.png" alt="Sword held normally" width="380">
<img src="docs/pose-blocking.png" alt="Sword raised in the old block stance" width="380">

<img src="docs/pose-third-person.png" alt="The block arm pose in third person" width="380">

*Right click held, third shot is F5. All three are straight out of the automated client test below.*

## What it actually is

This is the 1.8 block **stance**, and nothing else. Mojang removed sword blocking in 1.9 and
replaced it with shields; what they never removed is the pose itself — the renderer still knows how
to draw an item held in the old block position, swords just stopped ever asking for it. This mod
asks for it again.

Be clear about the limits, because this matters if you play PvP:

- It is **visual**. You take exactly the same damage as before. There is no 50% reduction, no
  knockback change, no hit cancelling.
- It runs **entirely on your client**. No packets are added or changed, the server is never told
  anything, and nobody else sees the pose. Only you need the mod; it works on vanilla servers,
  on Paper, on realms, on anything.
- Because it changes no gameplay and sends nothing, it is not a combat advantage. It is nostalgia.

If you want blocking that really reduces damage, that needs a server side mod and every player has
to install it — a different project.

## Install

1. [Fabric Loader](https://fabricmc.net/use/installer/) 0.19.3 or newer, for Minecraft 1.21.11.
2. [Fabric API](https://modrinth.com/mod/fabric-api) for 1.21.11 into `mods/`.
3. **[dist/old-sword-blocking-1.0.0.jar](dist/old-sword-blocking-1.0.0.jar)** into `mods/`
   (use the *Download raw file* button on GitHub).

Java 21 or newer, same as 1.21.11 itself.

## Using it

Hold right click while a sword is in your main hand. That is the whole thing.

The pose is deliberately suppressed when right click means something else, so it never lies to you:

| Situation | Pose |
|---|---|
| Sword in main hand, nothing else happening | shown |
| Any screen open (chest, chat, inventory), window unfocused | hidden |
| Eating, drawing a bow, raising a shield, using a spyglass | hidden |
| Placing a block from the off hand at a block you are looking at | hidden |
| Spectator | hidden |

Optional extras:

- **Keybind** — *Options → Controls → Gameplay → Toggle sword blocking*. Unbound by default so it
  cannot collide with a key you already use.
- **Commands** — `/oldswordblock status`, `/oldswordblock toggle`, `/oldswordblock reload`.
  These are client commands: they never reach the server.

## Config

`config/old-sword-blocking.json`, written on first launch. `/oldswordblock reload` re-reads it
without restarting the game.

| Key | Default | What it does |
|---|---|---|
| `enabled` | `true` | Master switch |
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

The pose defaults are not invented. They are Minecraft's own numbers for a non-shield item with
`UseAction.BLOCK`, which is the modern engine's direct descendant of 1.8's
`ItemRenderer#doBlockTransformations`. `offsetX`, `rotationY` and `rotationZ` are mirrored
automatically if you play left handed.

## How it works

Two mixins, both client only:

- `HeldItemRendererMixin` — at the head of `renderFirstPersonItem`, when the mod says you are
  blocking, it applies vanilla's own equip offset and swing, then the old block transform, then
  hands the stack straight back to vanilla's item renderer. Nothing about how the item is drawn is
  reimplemented.
- `PlayerEntityRendererMixin` — turns your own `ArmPose.ITEM` into `ArmPose.BLOCK` in third person,
  and only ever for the local player, so other people's models are untouched.

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

It boots an actual game, creates a creative world, puts a diamond sword in the hand, holds the use
key, and asserts that the mod enters the block state and leaves it again — including that an empty
hand never poses. Screenshots of each stage land in `run/screenshots/`.

Built and verified against Minecraft 1.21.11, Yarn 1.21.11+build.6, Loader 0.19.3,
Fabric API 0.141.6+1.21.11, Loom 1.17.20, Gradle 9.5.

## Compatibility

Anything else that mixes into `HeldItemRenderer#renderFirstPersonItem` at head and cancels
(some animation and "old animations" mods do) can conflict — whichever cancels first wins. If your
sword pose stops appearing after adding such a mod, that is the cause.

## Licence

MIT, same as the rest of this repository.
