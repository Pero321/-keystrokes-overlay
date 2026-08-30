package com.pero321.oldswordblocking.config;

import java.util.ArrayList;
import java.util.List;

/**
 * Every value here is written to {@code config/old-sword-blocking.json} and can be edited by hand.
 * The defaults reproduce the 1.8 sword block as closely as the modern renderer allows.
 */
public class ModConfig {

    /** Master switch. Toggled in game with the keybind or {@code /oldswordblock toggle}. */
    public boolean enabled = true;

    /** Show the block pose on your own hand (the view you actually play in). */
    public boolean firstPerson = true;

    /** Show the block arm pose on your own body in F5 / third person. */
    public boolean thirdPerson = true;

    /** Items that may be "blocked" with. */
    public boolean allowSwords = true;
    public boolean allowAxes = false;
    public boolean allowAnyItem = false;

    /** Extra item ids, e.g. "minecraft:trident" or "somemod:katana". */
    public List<String> extraItems = new ArrayList<>();

    /** Never pose while something is in the off hand (closest to 1.8, which had no off hand). */
    public boolean requireEmptyOffhand = false;

    /** Suppress the pose while right click is actually placing a block from the off hand. */
    public boolean suppressWhenPlacingFromOffhand = true;

    /** Keep the pose while the arm is mid swing. 1.8 did; set false if you prefer a clean swing. */
    public boolean allowWhileSwinging = true;

    /** Ticks it takes to slide into and out of the pose. 0 = instant, like 1.8. */
    public int transitionTicks = 2;

    /*
     * Pose tuning. The defaults are Minecraft's own numbers for a non-shield item with
     * UseAction.BLOCK (HeldItemRenderer#renderFirstPersonItem), which is the modern engine's
     * direct descendant of 1.8's ItemRenderer#doBlockTransformations. Change them if you want
     * the sword held higher, lower or at a different angle.
     */
    /** Sideways offset. Mirrored automatically for a left handed player. */
    public float offsetX = -0.14142136F;
    public float offsetY = 0.08F;
    public float offsetZ = 0.14142136F;
    public float rotationX = -102.25F;
    /** Mirrored automatically for a left handed player. */
    public float rotationY = 13.365F;
    /** Mirrored automatically for a left handed player. */
    public float rotationZ = 78.05F;
    public float scale = 1.0F;

    /** The glowing streak that follows the blade through a swing. */
    public TrailConfig trail = new TrailConfig();

    /** FPS, ping, and the gear durability strip. */
    public HudConfig hud = new HudConfig();

    public static class TrailConfig {
        public boolean enabled = true;

        /** How many rendered frames the streak spans. More = longer tail. */
        public int samples = 16;

        /** Colour of the streak, 0xRRGGBB. */
        public String color = "#8AE9FF";

        /** Opacity at the blade end, 0 to 1. The tail always fades to nothing. */
        public float opacity = 0.85F;

        /**
         * The two ends of the streak, in hand space: `near` is the hilt, `far` is the tip.
         * The defaults are where a vanilla sword's blade actually sits once the
         * `item/handheld` first person display transform has been applied, so the ribbon lies
         * along the blade. Tune them for a resource pack with unusual sword models.
         */
        public float nearX = 0.07F;
        public float nearY = -0.30F;
        public float nearZ = -0.12F;
        public float farX = 0.07F;
        public float farY = 0.80F;
        public float farZ = 0.28F;
    }

    public static class HudConfig {
        public boolean showFps = true;
        public boolean showPing = true;
        /** TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT or BOTTOM_RIGHT. */
        public String infoAnchor = "TOP_LEFT";
        /** Distance inwards from that corner, in pixels. */
        public int infoOffsetX = 4;
        public int infoOffsetY = 4;

        /** Armour and held tools with a durability bar under each. */
        public boolean showGear = true;
        public String gearAnchor = "BOTTOM_LEFT";
        public int gearOffsetX = 4;
        public int gearOffsetY = 4;
        /** Hide pieces that are still at full durability. */
        public boolean onlyDamagedGear = false;
        public boolean includeOffHand = true;

        /** At or below this much durability left, the piece gets a warning mark. */
        public int warnBelowPercent = 15;
        /** A one off chat line naming the piece the first time it drops that low. */
        public boolean warnInChat = true;
    }

    /** Clamp anything a hand edited file may have broken. */
    public void sanitise() {
        if (transitionTicks < 0) transitionTicks = 0;
        if (transitionTicks > 40) transitionTicks = 40;
        if (scale <= 0.0F) scale = 1.0F;
        if (extraItems == null) extraItems = new ArrayList<>();
        if (trail == null) trail = new TrailConfig();
        if (hud == null) hud = new HudConfig();
        trail.samples = Math.clamp(trail.samples, 2, 64);
        trail.opacity = Math.clamp(trail.opacity, 0.0F, 1.0F);
        hud.warnBelowPercent = Math.clamp(hud.warnBelowPercent, 1, 99);
    }
}
