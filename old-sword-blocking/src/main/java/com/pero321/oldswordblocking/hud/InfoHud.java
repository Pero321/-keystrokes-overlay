package com.pero321.oldswordblocking.hud;

import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.network.PlayerListEntry;
import net.minecraft.client.render.RenderTickCounter;

/**
 * One compact line: frame rate and round trip time, each number coloured by how healthy it is,
 * units dimmed so the eye lands on the digits. Both are read straight from the client; nothing is
 * measured or sent by this mod.
 */
public class InfoHud implements HudElement {

    private static final String SEPARATOR = " · ";

    @Override
    public void render(DrawContext context, RenderTickCounter tickCounter) {
        MinecraftClient client = MinecraftClient.getInstance();
        ModConfig.HudConfig config = ConfigManager.get().hud;

        if (!ConfigManager.get().enabled || client.player == null || client.options.hudHidden) {
            return;
        }
        // Behind an open screen the numbers are just clutter, and the F3 screen says all of this
        // already, bigger.
        if (client.currentScreen != null || client.getDebugHud().shouldShowDebugHud()) {
            return;
        }
        if (!config.showFps && !config.showPing) {
            return;
        }

        TextRenderer font = client.textRenderer;
        int fps = client.getCurrentFps();
        int ping = currentPing(client);

        int width = 0;
        if (config.showFps) {
            width += font.getWidth(String.valueOf(fps)) + font.getWidth(" fps");
        }
        if (config.showPing) {
            if (config.showFps) {
                width += font.getWidth(SEPARATOR);
            }
            width += font.getWidth(String.valueOf(ping)) + font.getWidth(" ms");
        }

        float scale = config.scale;
        HudAnchor anchor = HudAnchor.parse(config.infoAnchor);
        int screenWidth = Math.round(context.getScaledWindowWidth() / scale);
        int screenHeight = Math.round(context.getScaledWindowHeight() / scale);
        int pad = config.background ? HudTheme.PADDING : 0;
        int left = anchor.x(screenWidth, width, config.infoOffsetX + pad);
        int top = anchor.y(screenHeight, font.fontHeight, config.infoOffsetY + pad);

        context.getMatrices().pushMatrix();
        context.getMatrices().scale(scale, scale);

        if (config.background) {
            HudTheme.panel(context, left, top, width, font.fontHeight);
        }

        int x = left;
        if (config.showFps) {
            x = draw(context, font, config, String.valueOf(fps), x, top, fpsColor(fps));
            x = draw(context, font, config, " fps", x, top, HudTheme.LABEL);
        }
        if (config.showPing) {
            if (config.showFps) {
                x = draw(context, font, config, SEPARATOR, x, top, HudTheme.LABEL);
            }
            x = draw(context, font, config, String.valueOf(ping), x, top, pingColor(ping));
            draw(context, font, config, " ms", x, top, HudTheme.LABEL);
        }

        context.getMatrices().popMatrix();
    }

    private static int draw(DrawContext context, TextRenderer font, ModConfig.HudConfig config,
                            String text, int x, int y, int color) {
        HudTheme.text(context, font, text, x, y, color, config.outlineText);
        return x + font.getWidth(text);
    }

    private static int fpsColor(int fps) {
        if (fps >= 50) {
            return HudTheme.GOOD;
        }
        return fps >= 25 ? HudTheme.FAIR : HudTheme.BAD;
    }

    private static int pingColor(int ping) {
        if (ping <= 60) {
            return HudTheme.GOOD;
        }
        return ping <= 150 ? HudTheme.FAIR : HudTheme.BAD;
    }

    /** 0 while the player list has not arrived yet, which happens for a moment after joining. */
    private static int currentPing(MinecraftClient client) {
        if (client.getNetworkHandler() == null || client.player == null) {
            return 0;
        }
        PlayerListEntry entry = client.getNetworkHandler().getPlayerListEntry(client.player.getUuid());
        return entry == null ? 0 : Math.max(0, entry.getLatency());
    }
}
