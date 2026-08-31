package com.pero321.oldswordblocking.config;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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

    /** How each blade carries itself through a swing. */
    public SwingConfig swing = new SwingConfig();

    /** The glowing streak that follows the blade through a swing. */
    public TrailConfig trail = new TrailConfig();

    /** FPS, ping, and the gear durability strip. */
    public HudConfig hud = new HudConfig();

    /** Streaks behind thrown tridents and loosed arrows, and markers where they land. */
    public ProjectileConfig projectiles = new ProjectileConfig();

    public static class ProjectileConfig {
        /** The streak behind a projectile in flight. */
        public boolean trail = true;
        public boolean trailArrows = true;
        public boolean trailTridents = true;
        /** Half width of the streak, in blocks. */
        public float width = 0.09F;
        public int samples = 16;
        public float opacity = 0.75F;
        public int smoothing = 2;
        /** Tipped arrows streak in their potion's colour. */
        public boolean usePotionColor = true;

        /** A mark left where a projectile lands, so it can be found again. */
        public boolean markers = true;
        public boolean markArrows = true;
        public boolean markTridents = true;
        /** Only mark projectiles you fired yourself. */
        public boolean onlyMine = true;
        public int maxMarkers = 12;
        public int lifetimeSeconds = 240;

        /** A ring on the ground at the exact spot. The one you can always find. */
        public boolean ring = true;
        /** Radius of that ring, in blocks. */
        public float ringRadius = 0.45F;
        /** The exclamation mark floating above the spot. */
        public boolean mark = true;
        /** Drop the mark once you are this close; by then you can see the thing itself. */
        public float clearWithinBlocks = 3.0F;
        public float markerScale = 1.0F;
    }

    public static class SwingConfig {
        public boolean enabled = true;

        /** Give each material its own weight and arc. Off: one middling swing for everything. */
        public boolean perMaterial = true;

        /** 0 is vanilla's swing untouched, 1 the full effect. Dial the whole thing back here. */
        public float strength = 1.0F;

        /** Multiplies how much heavier blades wind up. */
        public float weight = 1.0F;

        /** Multiplies how far the arm travels. */
        public float arc = 1.0F;
    }

    public static class TrailConfig {
        public boolean enabled = true;

        /** How many rendered frames the streak spans. More = longer tail. */
        public int samples = 16;

        /**
         * Fallback colour, used for anything the material table below does not recognise.
         */
        public String color = "#8AE9FF";

        /** Give each sword material its own streak colour: wood dull, diamond cyan, and so on. */
        public boolean colorPerMaterial = true;

        /**
         * Per item overrides, e.g. {"somemod:katana": "#FF4D6D"}. Beats the material table.
         */
        public Map<String, String> colorsByItem = new HashMap<>();

        /** Opacity at the blade end, 0 to 1. The tail always fades to nothing. */
        public float opacity = 0.85F;

        /** Extra points inserted between frames, so a fast swing curves instead of faceting. */
        public int smoothing = 3;

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
        /** A soft panel behind each widget. Off by default: bare text sits lighter on the screen. */
        public boolean background = false;

        /** Ring the text in dark rather than dropping one shadow, so it survives any background. */
        public boolean outlineText = true;

        /** Size of the whole HUD. Worth raising on a phone, lowering on a very large screen. */
        public float scale = 1.0F;

        public boolean showFps = true;
        public boolean showPing = true;
        /** TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT or BOTTOM_RIGHT. */
        public String infoAnchor = "TOP_LEFT";
        /** Distance inwards from that corner, in pixels. */
        public int infoOffsetX = 4;
        public int infoOffsetY = 4;

        /** Armour and held tools with a durability bar under each. */
        public boolean showGear = true;
        public String gearAnchor = "BOTTOM_RIGHT";
        public int gearOffsetX = 4;
        public int gearOffsetY = 4;

        /** VERTICAL stacks the pieces down the side; HORIZONTAL lays them out in a row. */
        public String gearLayout = "VERTICAL";
        /** Hide pieces that are still at full durability. */
        public boolean onlyDamagedGear = false;

        /** The durability actually left on each piece, as a number, beside its icon. */
        public boolean showDurabilityNumbers = true;

        /** Add the maximum too, as "312/363". */
        public boolean showMaxDurability = false;

        /** The small durability bar. Redundant once the numbers are on, so off by default. */
        public boolean showBar = false;
        public boolean includeOffHand = true;

        /** At or below this much durability left, the piece gets a warning mark. */
        public int warnBelowPercent = 15;
        /** A one off chat line naming the piece the first time it drops that low. */
        public boolean warnInChat = true;

        /**
         * Shake a piece that is nearly gone, in short bursts, so it catches the eye even when the
         * exclamation mark does not. The closer to breaking, the harder and the more often.
         */
        public boolean shakeWhenLow = true;
    }

    /** Clamp anything a hand edited file may have broken. */
    public void sanitise() {
        if (transitionTicks < 0) transitionTicks = 0;
        if (transitionTicks > 40) transitionTicks = 40;
        if (scale <= 0.0F) scale = 1.0F;
        if (extraItems == null) extraItems = new ArrayList<>();
        if (swing == null) swing = new SwingConfig();
        swing.strength = Math.clamp(swing.strength, 0.0F, 1.0F);
        swing.weight = Math.clamp(swing.weight, 0.0F, 3.0F);
        swing.arc = Math.clamp(swing.arc, 0.0F, 3.0F);
        if (trail == null) trail = new TrailConfig();
        if (hud == null) hud = new HudConfig();
        if (trail.colorsByItem == null) trail.colorsByItem = new HashMap<>();
        trail.samples = Math.clamp(trail.samples, 2, 64);
        trail.smoothing = Math.clamp(trail.smoothing, 0, 8);
        if (projectiles == null) projectiles = new ProjectileConfig();
        projectiles.samples = Math.clamp(projectiles.samples, 2, 64);
        projectiles.smoothing = Math.clamp(projectiles.smoothing, 0, 8);
        projectiles.maxMarkers = Math.clamp(projectiles.maxMarkers, 1, 64);
        projectiles.markerScale = Math.clamp(projectiles.markerScale, 0.3F, 4.0F);
        projectiles.ringRadius = Math.clamp(projectiles.ringRadius, 0.15F, 4.0F);
        trail.opacity = Math.clamp(trail.opacity, 0.0F, 1.0F);
        hud.warnBelowPercent = Math.clamp(hud.warnBelowPercent, 1, 99);
        hud.scale = Math.clamp(hud.scale, 0.5F, 3.0F);
    }
}
