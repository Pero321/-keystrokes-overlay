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

    /** Clamp anything a hand edited file may have broken. */
    public void sanitise() {
        if (transitionTicks < 0) transitionTicks = 0;
        if (transitionTicks > 40) transitionTicks = 40;
        if (scale <= 0.0F) scale = 1.0F;
        if (extraItems == null) extraItems = new ArrayList<>();
    }
}
