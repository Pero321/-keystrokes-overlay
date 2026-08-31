package com.pero321.oldswordblocking.swing;

/**
 * How one kind of blade carries itself through a swing.
 *
 * @param weight how much the blade has to be hauled around: 0 flicks instantly, 1 winds up first
 *               and then falls through. Warps the timing, it does not change how long a swing lasts.
 * @param arc    how far the arm travels. Heavier blades cut a wider arc.
 * @param settle degrees of counter rotation as the blade lands, so weight reads on the follow
 *               through instead of the swing simply stopping.
 */
public record SwingProfile(float weight, float arc, float settle) {

    public static final SwingProfile VANILLA = new SwingProfile(0.0F, 1.0F, 0.0F);
    public static final SwingProfile DEFAULT = new SwingProfile(0.5F, 1.02F, 6.0F);

    /**
     * Blends toward vanilla by {@code strength}, then applies the global multipliers, so one
     * config value can dial the whole effect back without editing every profile.
     */
    public SwingProfile scaled(float strength, float weightScale, float arcScale) {
        float blend = Math.clamp(strength, 0.0F, 1.0F);
        return new SwingProfile(
                this.weight * blend * weightScale,
                1.0F + (this.arc - 1.0F) * blend * arcScale,
                this.settle * blend);
    }
}
