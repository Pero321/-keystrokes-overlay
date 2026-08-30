package com.pero321.oldswordblocking.trail;

import com.pero321.oldswordblocking.config.ModConfig;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.util.Identifier;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Gives every sword its own streak. Colours are picked to read against the world rather than to
 * match the item exactly — netherite's actual near black would be invisible as a trail, so it gets
 * the pale violet sheen the item has in bright light instead.
 */
public final class TrailPalette {

    /** Matched against the item id's path, longest sensible prefix first. */
    private static final Map<String, Integer> BY_MATERIAL = new LinkedHashMap<>();

    static {
        BY_MATERIAL.put("wooden_", 0xC79155);
        BY_MATERIAL.put("stone_", 0xBFBFBF);
        BY_MATERIAL.put("copper_", 0xE8874F);
        BY_MATERIAL.put("iron_", 0xE9EEF5);
        BY_MATERIAL.put("golden_", 0xFFD84D);
        BY_MATERIAL.put("diamond_", 0x7FF3E4);
        BY_MATERIAL.put("netherite_", 0xC0A8C8);
    }

    /** Whole items that are not "<material>_sword" shaped. */
    private static final Map<String, Integer> BY_ITEM = Map.of(
            "trident", 0x4FD8CF,
            "mace", 0x9A87C4);

    private TrailPalette() {
    }

    public static int colorFor(ItemStack stack, ModConfig.TrailConfig config) {
        Identifier id = Registries.ITEM.getId(stack.getItem());

        String override = config.colorsByItem.get(id.toString());
        if (override != null) {
            return parse(override, config);
        }
        if (!config.colorPerMaterial) {
            return parse(config.color, config);
        }

        String path = id.getPath();
        Integer exact = BY_ITEM.get(path);
        if (exact != null) {
            return exact;
        }
        for (Map.Entry<String, Integer> entry : BY_MATERIAL.entrySet()) {
            if (path.startsWith(entry.getKey())) {
                return entry.getValue();
            }
        }
        return parse(config.color, config);
    }

    private static int parse(String value, ModConfig.TrailConfig config) {
        if (value != null) {
            try {
                return Integer.parseInt(value.startsWith("#") ? value.substring(1) : value, 16) & 0xFFFFFF;
            } catch (NumberFormatException ignored) {
                // fall through to the built in default
            }
        }
        return 0x8AE9FF;
    }
}
