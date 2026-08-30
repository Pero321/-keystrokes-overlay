package com.pero321.oldswordblocking.hud;

import net.minecraft.client.gui.DrawContext;

/**
 * The few colours and the one panel shape both widgets share, so they read as one piece of UI
 * rather than two unrelated overlays.
 */
public final class HudTheme {

    public static final int PANEL = 0x90000000;
    public static final int PANEL_EDGE = 0x26FFFFFF;

    public static final int LABEL = 0xFF9AA0A6;
    public static final int VALUE = 0xFFF2F4F6;

    public static final int GOOD = 0xFF6ADE73;
    public static final int FAIR = 0xFFE3C34B;
    public static final int BAD = 0xFFE8615A;

    public static final int PADDING = 3;

    private HudTheme() {
    }

    /**
     * A soft panel behind a block of content: filled body, plus lighter top and bottom edges that
     * read as a highlight without needing a real border.
     */
    public static void panel(DrawContext context, int x, int y, int width, int height) {
        int left = x - PADDING;
        int top = y - PADDING;
        int right = x + width + PADDING;
        int bottom = y + height + PADDING;

        context.fill(left + 1, top, right - 1, bottom, PANEL);
        context.fill(left, top + 1, left + 1, bottom - 1, PANEL);
        context.fill(right - 1, top + 1, right, bottom - 1, PANEL);
        context.fill(left + 1, top, right - 1, top + 1, PANEL_EDGE);
        context.fill(left + 1, bottom - 1, right - 1, bottom, PANEL_EDGE);
    }

    /** Green when there is plenty, amber in the middle, red when it is nearly gone. */
    public static int forPercent(int percent) {
        if (percent > 50) {
            return GOOD;
        }
        return percent > 20 ? FAIR : BAD;
    }
}
