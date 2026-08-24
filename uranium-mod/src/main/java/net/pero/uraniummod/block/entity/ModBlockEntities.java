package net.pero.uraniummod.block.entity;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;
import net.pero.uraniummod.block.ModBlocks;

public class ModBlockEntities {
	public static final BlockEntityType<CentrifugeBlockEntity> CENTRIFUGE = Registry.register(
			Registries.BLOCK_ENTITY_TYPE,
			Identifier.of(UraniumMod.MOD_ID, "centrifuge"),
			FabricBlockEntityTypeBuilder.create(CentrifugeBlockEntity::new, ModBlocks.CENTRIFUGE).build()
	);

	public static void registerBlockEntities() {
		UraniumMod.LOGGER.info("Registering block entities for " + UraniumMod.MOD_ID);
	}
}
