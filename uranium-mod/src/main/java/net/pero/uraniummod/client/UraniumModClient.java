package net.pero.uraniummod.client;

import net.fabricmc.api.ClientModInitializer;
import net.minecraft.client.gui.screen.ingame.HandledScreens;
import net.pero.uraniummod.client.screen.CentrifugeScreen;
import net.pero.uraniummod.screen.ModScreenHandlers;

public class UraniumModClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		HandledScreens.register(ModScreenHandlers.CENTRIFUGE, CentrifugeScreen::new);
	}
}
