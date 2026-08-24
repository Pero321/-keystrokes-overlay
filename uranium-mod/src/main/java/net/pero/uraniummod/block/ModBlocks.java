package net.pero.uraniummod.block;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.Blocks;
import net.minecraft.block.ExperienceDroppingBlock;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.intprovider.UniformIntProvider;
import net.pero.uraniummod.UraniumMod;

import java.util.function.Function;

public class ModBlocks {
	public static final Block URANIUM_ORE = register(
			"uranium_ore",
			settings -> new ExperienceDroppingBlock(UniformIntProvider.create(3, 7), settings),
			AbstractBlock.Settings.create()
					.strength(3.0f, 3.0f)
					.requiresTool()
					.sounds(BlockSoundGroup.STONE)
	);

	public static final Block DEEPSLATE_URANIUM_ORE = register(
			"deepslate_uranium_ore",
			settings -> new ExperienceDroppingBlock(UniformIntProvider.create(3, 7), settings),
			AbstractBlock.Settings.create()
					.strength(4.5f, 3.0f)
					.requiresTool()
					.sounds(BlockSoundGroup.DEEPSLATE)
	);

	public static final Block RAW_URANIUM_BLOCK = register(
			"raw_uranium_block",
			Block::new,
			AbstractBlock.Settings.copy(Blocks.RAW_IRON_BLOCK)
	);

	public static final Block URANIUM_BLOCK = register(
			"uranium_block",
			Block::new,
			AbstractBlock.Settings.copy(Blocks.IRON_BLOCK)
	);

	public static final Block CENTRIFUGE = register(
			"centrifuge",
			CentrifugeBlock::new,
			AbstractBlock.Settings.create()
					.strength(3.5f, 6.0f)
					.requiresTool()
					.sounds(BlockSoundGroup.METAL)
					.luminance(state -> state.get(CentrifugeBlock.LIT) ? 8 : 0)
	);

	/**
	 * Registers a block plus its matching {@link BlockItem}. Since 1.21.2 both the block and the
	 * item have to know their own registry key before they are constructed, hence the factory.
	 */
	private static Block register(String name, Function<AbstractBlock.Settings, Block> factory,
	                              AbstractBlock.Settings settings) {
		Identifier id = Identifier.of(UraniumMod.MOD_ID, name);

		RegistryKey<Block> blockKey = RegistryKey.of(RegistryKeys.BLOCK, id);
		Block block = factory.apply(settings.registryKey(blockKey));
		Registry.register(Registries.BLOCK, blockKey, block);

		RegistryKey<Item> itemKey = RegistryKey.of(RegistryKeys.ITEM, id);
		BlockItem blockItem = new BlockItem(block, new Item.Settings().registryKey(itemKey));
		Registry.register(Registries.ITEM, itemKey, blockItem);

		return block;
	}

	public static void registerModBlocks() {
		UraniumMod.LOGGER.info("Registering blocks for " + UraniumMod.MOD_ID);
	}
}
