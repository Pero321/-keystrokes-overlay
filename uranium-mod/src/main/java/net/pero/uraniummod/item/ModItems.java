package net.pero.uraniummod.item;

import net.minecraft.item.Item;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;

import java.util.function.Function;

public class ModItems {
	public static final Item RAW_URANIUM = register("raw_uranium", Item::new, new Item.Settings());
	public static final Item URANIUM_INGOT = register("uranium_ingot", Item::new, new Item.Settings());

	private static Item register(String name, Function<Item.Settings, Item> factory, Item.Settings settings) {
		RegistryKey<Item> itemKey = RegistryKey.of(RegistryKeys.ITEM, Identifier.of(UraniumMod.MOD_ID, name));
		Item item = factory.apply(settings.registryKey(itemKey));
		Registry.register(Registries.ITEM, itemKey, item);
		return item;
	}

	public static void registerModItems() {
		UraniumMod.LOGGER.info("Registering items for " + UraniumMod.MOD_ID);
	}
}
