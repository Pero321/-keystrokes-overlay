package net.pero.uraniummod.world;

import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.util.Identifier;
import net.minecraft.world.gen.feature.PlacedFeature;
import net.pero.uraniummod.UraniumMod;

/**
 * Keys for the placed features defined as JSON under
 * {@code data/uraniummod/worldgen/placed_feature/}.
 */
public class ModPlacedFeatures {
	public static final RegistryKey<PlacedFeature> URANIUM_ORE_PLACED_KEY = of("uranium_ore_placed");
	public static final RegistryKey<PlacedFeature> URANIUM_ORE_BURIED_PLACED_KEY = of("uranium_ore_buried_placed");

	private static RegistryKey<PlacedFeature> of(String name) {
		return RegistryKey.of(RegistryKeys.PLACED_FEATURE, Identifier.of(UraniumMod.MOD_ID, name));
	}
}
