package com.pero321.oldswordblocking.hud;

/**
 * Which corner a HUD block hangs off. Offsets are always measured inwards from that corner, so
 * moving a widget never needs negative numbers in the config.
 */
public enum HudAnchor {
    TOP_LEFT(false, false),
    TOP_RIGHT(true, false),
    BOTTOM_LEFT(false, true),
    BOTTOM_RIGHT(true, true);

    private final boolean right;
    private final boolean bottom;

    HudAnchor(boolean right, boolean bottom) {
        this.right = right;
        this.bottom = bottom;
    }

    public static HudAnchor parse(String name) {
        if (name != null) {
            for (HudAnchor anchor : values()) {
                if (anchor.name().equalsIgnoreCase(name)) {
                    return anchor;
                }
            }
        }
        return TOP_LEFT;
    }

    /** Left edge of a block `width` wide, `offset` pixels in from this corner. */
    public int x(int screenWidth, int width, int offset) {
        return this.right ? screenWidth - width - offset : offset;
    }

    /** Top edge of a block `height` tall, `offset` pixels in from this corner. */
    public int y(int screenHeight, int height, int offset) {
        return this.bottom ? screenHeight - height - offset : offset;
    }

    public boolean isRightAligned() {
        return this.right;
    }
}
