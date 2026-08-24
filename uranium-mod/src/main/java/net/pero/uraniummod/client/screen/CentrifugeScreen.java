package net.pero.uraniummod.client.screen;

import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;
import net.pero.uraniummod.screen.CentrifugeScreenHandler;

public class CentrifugeScreen extends HandledScreen<CentrifugeScreenHandler> {
	private static final Identifier TEXTURE =
			Identifier.of(UraniumMod.MOD_ID, "textures/gui/centrifuge.png");

	// must match the layout written by tools/gen_textures.py
	private static final int HEAT_X = 25, HEAT_Y = 17, HEAT_W = 12, HEAT_H = 52;
	private static final int ARROW_X = 79, ARROW_Y = 34, ARROW_W = 24, ARROW_H = 17;
	private static final int HEAT_U = 200, ARROW_U = 176;

	public CentrifugeScreen(CentrifugeScreenHandler handler, PlayerInventory inventory, Text title) {
		super(handler, inventory, title);
	}

	// the console panel is dark, so the default near-black label colour is unreadable
	private static final int TITLE_COLOUR = 0xF0E4CE;
	private static final int LABEL_COLOUR = 0xB9B2A5;

	@Override
	protected void init() {
		super.init();
		titleY = 5;
		playerInventoryTitleY = backgroundHeight - 94;
	}

	@Override
	protected void drawForeground(DrawContext context, int mouseX, int mouseY) {
		context.drawText(textRenderer, title, titleX, titleY, TITLE_COLOUR, false);
		context.drawText(textRenderer, playerInventoryTitle,
				playerInventoryTitleX, playerInventoryTitleY, LABEL_COLOUR, false);
	}

	@Override
	protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
		int x = (width - backgroundWidth) / 2;
		int y = (height - backgroundHeight) / 2;

		context.drawTexture(RenderLayer::getGuiTextured, TEXTURE, x, y, 0, 0,
				backgroundWidth, backgroundHeight, 256, 256);

		// heat gauge fills from the bottom up
		int heat = Math.min(HEAT_H, handler.getHeatScaled(HEAT_H));
		if (heat > 0) {
			context.drawTexture(RenderLayer::getGuiTextured, TEXTURE,
					x + HEAT_X, y + HEAT_Y + (HEAT_H - heat),
					HEAT_U, HEAT_H - heat, HEAT_W, heat, 256, 256);
		}

		int progress = Math.min(ARROW_W, handler.getProgressScaled(ARROW_W));
		if (progress > 0) {
			context.drawTexture(RenderLayer::getGuiTextured, TEXTURE,
					x + ARROW_X, y + ARROW_Y, ARROW_U, 0, progress, ARROW_H, 256, 256);
		}
	}

	@Override
	public void render(DrawContext context, int mouseX, int mouseY, float delta) {
		super.render(context, mouseX, mouseY, delta);
		drawMouseoverTooltip(context, mouseX, mouseY);

		int x = (width - backgroundWidth) / 2;
		int y = (height - backgroundHeight) / 2;
		if (mouseX >= x + HEAT_X && mouseX < x + HEAT_X + HEAT_W
				&& mouseY >= y + HEAT_Y && mouseY < y + HEAT_Y + HEAT_H) {
			int percent = handler.getHeat() * 100 / Math.max(1, handler.getMaxHeat());
			Text status = handler.isHotEnough()
					? Text.translatable("screen.uraniummod.centrifuge.ready").formatted(Formatting.GREEN)
					: Text.translatable("screen.uraniummod.centrifuge.warming").formatted(Formatting.GRAY);
			context.drawTooltip(textRenderer,
					java.util.List.of(
							Text.translatable("screen.uraniummod.centrifuge.heat", percent),
							status),
					mouseX, mouseY);
		}
	}
}
