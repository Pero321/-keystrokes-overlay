package net.pero.uraniummod;

import net.fabricmc.api.ModInitializer;
import net.pero.uraniummod.block.ModBlocks;
import net.pero.uraniummod.item.ModItemGroups;
import net.pero.uraniummod.item.ModItems;
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
		ModItemGroups.registerItemGroups();
		ModWorldGeneration.generateModWorldGen();

		LOGGER.info("Uranium Ore loaded.");
	}
}
