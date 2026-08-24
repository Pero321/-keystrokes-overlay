package net.pero.uraniummod.item;

import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemGroups;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;
import net.pero.uraniummod.block.ModBlocks;

public class ModItemGroups {
	public static final RegistryKey<ItemGroup> URANIUM_GROUP_KEY =
			RegistryKey.of(RegistryKeys.ITEM_GROUP, Identifier.of(UraniumMod.MOD_ID, "uranium"));

	public static final ItemGroup URANIUM_GROUP = FabricItemGroup.builder()
			.icon(() -> new ItemStack(ModItems.RAW_URANIUM))
			.displayName(Text.translatable("itemGroup.uraniummod.uranium"))
			.build();

	public static void registerItemGroups() {
		Registry.register(Registries.ITEM_GROUP, URANIUM_GROUP_KEY, URANIUM_GROUP);

		ItemGroupEvents.modifyEntriesEvent(URANIUM_GROUP_KEY).register(entries -> {
			entries.add(ModBlocks.URANIUM_ORE);
			entries.add(ModBlocks.DEEPSLATE_URANIUM_ORE);
			entries.add(ModItems.RAW_URANIUM);
			entries.add(ModBlocks.RAW_URANIUM_BLOCK);
			entries.add(ModItems.URANIUM_INGOT);
			entries.add(ModBlocks.URANIUM_BLOCK);
			entries.add(ModBlocks.CENTRIFUGE);
		});

		// Also surface everything in the vanilla creative tabs, next to the vanilla equivalents.
		ItemGroupEvents.modifyEntriesEvent(ItemGroups.NATURAL).register(entries -> {
			entries.add(ModBlocks.URANIUM_ORE);
			entries.add(ModBlocks.DEEPSLATE_URANIUM_ORE);
		});

		ItemGroupEvents.modifyEntriesEvent(ItemGroups.INGREDIENTS).register(entries -> {
			entries.add(ModItems.RAW_URANIUM);
			entries.add(ModItems.URANIUM_INGOT);
		});

		ItemGroupEvents.modifyEntriesEvent(ItemGroups.BUILDING_BLOCKS).register(entries -> {
			entries.add(ModBlocks.RAW_URANIUM_BLOCK);
			entries.add(ModBlocks.URANIUM_BLOCK);
		});

		ItemGroupEvents.modifyEntriesEvent(ItemGroups.FUNCTIONAL).register(entries ->
				entries.add(ModBlocks.CENTRIFUGE));
		ItemGroupEvents.modifyEntriesEvent(ItemGroups.REDSTONE).register(entries ->
				entries.add(ModBlocks.CENTRIFUGE));
	}
}
