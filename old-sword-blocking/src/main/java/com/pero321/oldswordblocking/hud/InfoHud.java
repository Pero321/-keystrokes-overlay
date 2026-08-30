package com.pero321.oldswordblocking.hud;

import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.network.PlayerListEntry;
import net.minecraft.client.render.RenderTickCounter;

import java.util.ArrayList;
import java.util.List;

/**
 * Two lines of the numbers you actually keep glancing at: frame rate and round trip time to the
 * server. Both are read straight from the client; nothing is measured or sent by this mod.
 */
public class InfoHud implements HudElement {

    private static final int LINE_HEIGHT = 10;
    private static final int SHADOW_TEXT = 0xFFFFFFFF;

    @Override
    public void render(DrawContext context, RenderTickCounter tickCounter) {
        MinecraftClient client = MinecraftClient.getInstance();
        ModConfig.HudConfig config = ConfigManager.get().hud;

        if (!ConfigManager.get().enabled || client.player == null || client.options.hudHidden) {
            return;
        }
        if (client.getDebugHud().shouldShowDebugHud()) {
            // The F3 screen already says all of this, and says it bigger.
            return;
        }

        List<String> lines = new ArrayList<>(2);
        if (config.showFps) {
            lines.add(client.getCurrentFps() + " fps");
        }
        if (config.showPing) {
            lines.add(currentPing(client) + " ms");
        }
        if (lines.isEmpty()) {
            return;
        }

        TextRenderer font = client.textRenderer;
        HudAnchor anchor = HudAnchor.parse(config.infoAnchor);

        int width = 0;
        for (String line : lines) {
            width = Math.max(width, font.getWidth(line));
        }
        int left = anchor.x(context, width, config.infoOffsetX);
        int top = anchor.y(context, lines.size() * LINE_HEIGHT, config.infoOffsetY);

        for (int i = 0; i < lines.size(); i++) {
            String line = lines.get(i);
            int x = anchor.isRightAligned() ? left + width - font.getWidth(line) : left;
            context.drawTextWithShadow(font, line, x, top + i * LINE_HEIGHT, SHADOW_TEXT);
        }
    }

    /** -1 while the player list has not arrived yet, which happens for a moment after joining. */
    private static int currentPing(MinecraftClient client) {
        if (client.getNetworkHandler() == null || client.player == null) {
            return 0;
        }
        PlayerListEntry entry = client.getNetworkHandler().getPlayerListEntry(client.player.getUuid());
        return entry == null ? 0 : Math.max(0, entry.getLatency());
    }
}
