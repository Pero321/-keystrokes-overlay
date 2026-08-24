package net.pero.uraniummod.screen;

import net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.screen.ScreenHandlerType;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.pero.uraniummod.UraniumMod;

public class ModScreenHandlers {
	public static final ScreenHandlerType<CentrifugeScreenHandler> CENTRIFUGE = Registry.register(
			Registries.SCREEN_HANDLER,
			Identifier.of(UraniumMod.MOD_ID, "centrifuge"),
			new ExtendedScreenHandlerType<>(CentrifugeScreenHandler::new, BlockPos.PACKET_CODEC)
	);

	public static void registerScreenHandlers() {
		UraniumMod.LOGGER.info("Registering screen handlers for " + UraniumMod.MOD_ID);
	}
}
