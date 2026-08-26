package net.pero.uraniummod;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.registry.FuelRegistryEvents;
import net.pero.uraniummod.block.ModBlocks;
import net.pero.uraniummod.block.entity.ModBlockEntities;
import net.pero.uraniummod.item.ModItemGroups;
import net.pero.uraniummod.item.ModItems;
import net.pero.uraniummod.effect.ModEffects;
import net.pero.uraniummod.effect.RadiationHandler;
import net.pero.uraniummod.particle.ModParticles;
import net.pero.uraniummod.recipe.ModRecipes;
import net.pero.uraniummod.screen.ModScreenHandlers;
import net.pero.uraniummod.world.gen.ModWorldGeneration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UraniumMod implements ModInitializer {
	public static final String MOD_ID = "uraniummod";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		ModItems.registerModItems();
		ModBlocks.registerModBlocks();
		ModBlockEntities.registerBlockEntities();
		ModScreenHandlers.registerScreenHandlers();
		ModParticles.registerParticles();
		ModRecipes.register();
		ModEffects.register();
		ModItemGroups.registerItemGroups();
		ModWorldGeneration.generateModWorldGen();
		RadiationHandler.register();
		registerFuels();

		LOGGER.info("Uranium Ore loaded.");
	}

	/**
	 * Burn time for one fuel cell, in ticks: 160 items smelted, against a lava
	 * bucket's 100. The best fuel in the game, which is the point of spending a
	 * U-235 on it.
	 *
	 * <p>The ceiling is not a balance choice. A furnace stores its burn time as
	 * an NBT <em>short</em>, so anything past 32767 wraps negative and the
	 * furnace silently never lights -- the first version of this asked for
	 * 40000 and produced a fuel that could not be burned.
	 */
	public static final int FUEL_CELL_BURN_TICKS = 32000;

	private static void registerFuels() {
		FuelRegistryEvents.BUILD.register((builder, context) ->
				builder.add(ModItems.URANIUM_FUEL_CELL, FUEL_CELL_BURN_TICKS));
	}
}
