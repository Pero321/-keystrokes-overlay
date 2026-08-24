# Uranium Ore — Minecraft 1.21.4 (Fabric)

Adds uranium to the overworld: ore in both stone and deepslate, raw uranium,
uranium ingots, and the two matching storage blocks.

![textures](docs/textures.png)

## Contents

| Thing | ID | Notes |
| --- | --- | --- |
| Uranium Ore | `uraniummod:uranium_ore` | Hardness 3.0, drops 1–2 raw uranium |
| Deepslate Uranium Ore | `uraniummod:deepslate_uranium_ore` | Hardness 4.5, drops 1–2 raw uranium |
| Raw Uranium | `uraniummod:raw_uranium` | Smelts into an ingot |
| Uranium Ingot | `uraniummod:uranium_ingot` | |
| Block of Raw Uranium | `uraniummod:raw_uranium_block` | 9× raw uranium |
| Block of Uranium | `uraniummod:uranium_block` | 9× ingot |

Everything appears in its own **Uranium** creative tab, and is also mixed into
the vanilla Natural / Ingredients / Building Blocks tabs.

### Mining

Both ores need an **iron pickaxe or better** — mining with stone or wood drops
nothing. Fortune works (`ore_drops` formula, same as vanilla iron/copper), and
Silk Touch drops the ore block itself. Breaking an ore drops 3–7 XP.

### World generation

Uranium is deliberately rarer and deeper than iron. Two placements are added to
every overworld biome in the `UNDERGROUND_ORES` step:

- `uranium_ore_placed` — 2 veins/chunk, size 5, trapezoid distribution from
  y=-64 to y=8, 50% discard when exposed to air.
- `uranium_ore_buried_placed` — 3 veins/chunk, size 6, uniform from y=-64 to
  y=16, always discarded when exposed to air (so it hides in solid rock).

Measured on a freshly generated world (49 spawn chunks, seed `uraniumtest`):

```
uraniummod:uranium_ore                92    1.9 per chunk
uraniummod:deepslate_uranium_ore     671   13.7 per chunk
                                    ----   ----
                          uranium    763   15.6 per chunk

for reference, in the same chunks:
minecraft:iron_ore    + deepslate   3588   73.2 per chunk
minecraft:diamond_ore + deepslate   1110   22.7 per chunk
```

So it lands rarer than diamond and about a fifth as common as iron. By depth:

```
y  10..19    ############
y   0..9     #####################
y -10..-1    ######################################
y -20..-11   #################################
y -30..-21   ########################################
y -40..-31   ############################################
y -50..-41   ###############################
y -60..-51   ####################
y -64..-61   ###
```

In practice it is most common between y=-50 and y=0, peaking around y=-35, and
you will rarely see it exposed on a cave wall.

`tools/verify_worldgen.py` reproduces those numbers — it parses the generated
region files directly and counts placed blocks.

### Recipes

- Raw uranium → uranium ingot (furnace, 200 ticks / blast furnace, 100 ticks, 0.9 xp)
- 9 raw uranium ⇄ block of raw uranium
- 9 uranium ingot ⇄ block of uranium

## Installing

A prebuilt jar is committed at
[`dist/uranium-ore-1.0.0.jar`](dist/uranium-ore-1.0.0.jar).

1. Minecraft **1.21.4** with **Fabric Loader** 0.16.0 or newer.
2. Install [Fabric API](https://modrinth.com/mod/fabric-api) for 1.21.4 — this
   mod will not load without it.
3. Drop `uranium-ore-1.0.0.jar` into your `mods/` folder.

Works on both client and server (`"environment": "*"`). On a multiplayer server
it must be installed on the server; clients need it too, for the textures.

## Building from source

Requires JDK 21. The Gradle wrapper pulls everything else down.

```bash
cd uranium-mod
./gradlew build
```

The jar lands in `build/libs/uranium-ore-1.0.0.jar`. Ignore the
`-sources.jar` next to it.

To try it in a dev environment:

```bash
./gradlew runClient    # or runServer
```

### Versions

| | |
| --- | --- |
| Minecraft | 1.21.4 |
| Yarn mappings | 1.21.4+build.8 |
| Fabric Loader | 0.19.3 |
| Fabric API | 0.119.4+1.21.4 |
| Fabric Loom | 1.14.9 (needs Gradle 9.2+) |

## Textures

The six 16×16 textures are generated procedurally by
`tools/gen_textures.py` (pure Python, no dependencies) rather than being
hand-drawn, so the palette can be retuned in one place. Re-run it to
regenerate everything:

```bash
python3 tools/gen_textures.py
```

## Layout

```
src/main/java/net/pero/uraniummod/
  UraniumMod.java              entrypoint
  block/ModBlocks.java         the four blocks + their BlockItems
  item/ModItems.java           raw uranium, uranium ingot
  item/ModItemGroups.java      creative tabs
  world/ModPlacedFeatures.java registry keys for the placed features
  world/gen/ModWorldGeneration.java  adds them to overworld biomes

src/main/resources/
  assets/uraniummod/...        models, blockstates, textures, lang
  data/uraniummod/...          loot tables, recipes, worldgen JSON
  data/minecraft/tags/...      mineable/pickaxe, needs_iron_tool
```

Note that on 1.21.4 every item needs both a model in
`assets/uraniummod/models/item/` **and** an item-model definition in
`assets/uraniummod/items/` — the second directory is the 1.21.4 item model
system, and items render as missing-texture without it.

## License

MIT — see `LICENSE`.
