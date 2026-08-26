package net.pero.uraniummod.item;

import net.minecraft.item.ArmorItem;
import net.minecraft.item.AxeItem;
import net.minecraft.item.HoeItem;
import net.minecraft.item.Item;
import net.minecraft.item.PickaxeItem;
import net.minecraft.item.ShovelItem;
import net.minecraft.item.SwordItem;
import net.minecraft.item.ToolMaterial;
import net.minecraft.item.equipment.ArmorMaterial;
import net.minecraft.item.equipment.EquipmentAsset;
import net.minecraft.item.equipment.EquipmentAssetKeys;
import net.minecraft.item.equipment.EquipmentType;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;

import java.util.Map;
import java.util.function.Function;

public class ModItems {

	/** Repair material for uranium tools. */
	public static final TagKey<Item> URANIUM_INGOTS =
			TagKey.of(RegistryKeys.ITEM, Identifier.of(UraniumMod.MOD_ID, "uranium_ingots"));
	/** Repair material for the shielded suit. */
	public static final TagKey<Item> SHIELDING =
			TagKey.of(RegistryKeys.ITEM, Identifier.of(UraniumMod.MOD_ID, "shielding"));

	/**
	 * Sits between diamond and netherite: it mines everything diamond can, lasts
	 * longer, and hits slightly harder, but it is not a netherite replacement --
	 * it cannot mine what only netherite can, and it burns.
	 */
	public static final ToolMaterial URANIUM_TOOL_MATERIAL = new ToolMaterial(
			BlockTags.INCORRECT_FOR_DIAMOND_TOOL,
			2200,   // durability (diamond 1561, netherite 2031)
			9.0f,   // mining speed
			3.5f,   // attack damage bonus
			12,     // enchantability
			URANIUM_INGOTS);

	public static final RegistryKey<EquipmentAsset> SHIELDED_ARMOR_ASSET =
			RegistryKey.of(EquipmentAssetKeys.REGISTRY_KEY, Identifier.of(UraniumMod.MOD_ID, "shielded"));

	/**
	 * Protective gear, not combat gear: iron-grade defence and no toughness. What
	 * it is actually for is stopping radiation, which is handled outside the
	 * armour system entirely.
	 */
	public static final ArmorMaterial SHIELDED_ARMOR_MATERIAL = new ArmorMaterial(
			28,     // durability multiplier (iron 15, diamond 33)
			Map.of(
					EquipmentType.HELMET, 2,
					EquipmentType.CHESTPLATE, 6,
					EquipmentType.LEGGINGS, 5,
					EquipmentType.BOOTS, 2),
			9,      // enchantability
			SoundEvents.ITEM_ARMOR_EQUIP_IRON,
			0.0f,   // toughness
			0.0f,   // knockback resistance
			SHIELDING,
			SHIELDED_ARMOR_ASSET);

	// ------------------------------------------------------------------ materials

	public static final Item RAW_URANIUM = register("raw_uranium", Item::new, new Item.Settings());
	public static final Item URANIUM_INGOT = register("uranium_ingot", Item::new, new Item.Settings());

	/** The bulk product of enrichment -- common, and what the shielded suit is made of. */
	public static final Item URANIUM_238 = register("uranium_238", Item::new, new Item.Settings());
	/** The rare product of enrichment. Fissile, and the only thing that fuels a cell. */
	public static final Item URANIUM_235 = register("uranium_235", Item::new, new Item.Settings());

	/** Furnace fuel. Burns for a very long time -- see UraniumMod's fuel registration. */
	public static final Item URANIUM_FUEL_CELL =
			register("uranium_fuel_cell", Item::new, new Item.Settings());

	// ------------------------------------------------------------------ tools

	public static final Item URANIUM_SWORD = register("uranium_sword",
			settings -> new SwordItem(URANIUM_TOOL_MATERIAL, 3.0f, -2.4f, settings),
			new Item.Settings());
	public static final Item URANIUM_PICKAXE = register("uranium_pickaxe",
			settings -> new PickaxeItem(URANIUM_TOOL_MATERIAL, 1.0f, -2.8f, settings),
			new Item.Settings());
	public static final Item URANIUM_AXE = register("uranium_axe",
			settings -> new AxeItem(URANIUM_TOOL_MATERIAL, 5.0f, -3.0f, settings),
			new Item.Settings());
	public static final Item URANIUM_SHOVEL = register("uranium_shovel",
			settings -> new ShovelItem(URANIUM_TOOL_MATERIAL, 1.5f, -3.0f, settings),
			new Item.Settings());
	public static final Item URANIUM_HOE = register("uranium_hoe",
			settings -> new HoeItem(URANIUM_TOOL_MATERIAL, -3.0f, 0.0f, settings),
			new Item.Settings());

	// ------------------------------------------------------------------ armour

	public static final Item SHIELDED_HELMET = registerArmor("shielded_helmet", EquipmentType.HELMET);
	public static final Item SHIELDED_CHESTPLATE = registerArmor("shielded_chestplate", EquipmentType.CHESTPLATE);
	public static final Item SHIELDED_LEGGINGS = registerArmor("shielded_leggings", EquipmentType.LEGGINGS);
	public static final Item SHIELDED_BOOTS = registerArmor("shielded_boots", EquipmentType.BOOTS);

	private static Item registerArmor(String name, EquipmentType type) {
		return register(name,
				settings -> new ArmorItem(SHIELDED_ARMOR_MATERIAL, type, settings),
				new Item.Settings().maxDamage(type.getMaxDamage(SHIELDED_ARMOR_MATERIAL.durability())));
	}

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
