package net.pero.uraniummod.world.gen;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.minecraft.world.gen.GenerationStep;
import net.pero.uraniummod.world.ModPlacedFeatures;

public class ModWorldGeneration {
	public static void generateModWorldGen() {
		BiomeModifications.addFeature(
				BiomeSelectors.foundInOverworld(),
				GenerationStep.Feature.UNDERGROUND_ORES,
				ModPlacedFeatures.URANIUM_ORE_PLACED_KEY
		);

		BiomeModifications.addFeature(
				BiomeSelectors.foundInOverworld(),
				GenerationStep.Feature.UNDERGROUND_ORES,
				ModPlacedFeatures.URANIUM_ORE_BURIED_PLACED_KEY
		);
	}
}
