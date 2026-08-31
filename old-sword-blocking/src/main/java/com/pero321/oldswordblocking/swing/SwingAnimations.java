package com.pero321.oldswordblocking.swing;

import com.pero321.oldswordblocking.config.ModConfig;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Gives every blade its own swing.
 *
 * <p>This is vanilla's own swing, re-parameterised rather than replaced: the same translation and
 * the same three rotations, with three knobs on top. A wooden sword flicks out and back; a
 * netherite one winds up, falls through a wider arc and settles at the end. The swing still lasts
 * exactly as long as vanilla's, because its length is the attack animation the server drives —
 * only the shape of the motion inside those ticks changes.
 */
public final class SwingAnimations {

    /** Matched against the item id's path. */
    private static final Map<String, SwingProfile> BY_MATERIAL = new LinkedHashMap<>();

    static {
        BY_MATERIAL.put("golden_", new SwingProfile(0.05F, 0.90F, 2.0F));
        BY_MATERIAL.put("wooden_", new SwingProfile(0.12F, 0.93F, 3.0F));
        BY_MATERIAL.put("stone_", new SwingProfile(0.35F, 1.00F, 5.0F));
        BY_MATERIAL.put("copper_", new SwingProfile(0.40F, 1.02F, 5.0F));
        BY_MATERIAL.put("iron_", new SwingProfile(0.52F, 1.05F, 6.0F));
        BY_MATERIAL.put("diamond_", new SwingProfile(0.70F, 1.10F, 8.0F));
        BY_MATERIAL.put("netherite_", new SwingProfile(0.90F, 1.16F, 11.0F));
    }

    private static final Map<String, SwingProfile> BY_ITEM = Map.of(
            "trident", new SwingProfile(0.75F, 1.08F, 8.0F),
            "mace", new SwingProfile(1.00F, 1.25F, 14.0F));

    private SwingAnimations() {
    }

    public static SwingProfile profileFor(ItemStack stack, ModConfig.SwingConfig config) {
        Identifier id = Registries.ITEM.getId(stack.getItem());
        return profileForPath(id.getPath(), config);
    }

    /**
     * The profile for an item id's path, e.g. {@code netherite_sword}. Split out from
     * {@link #profileFor} so the swing can be measured outside a running game — see
     * {@code tools/SwingProbe.java}.
     */
    public static SwingProfile profileForPath(String path, ModConfig.SwingConfig config) {
        return lookup(path, config).scaled(config.strength, config.weight, config.arc);
    }

    private static SwingProfile lookup(String path, ModConfig.SwingConfig config) {
        if (!config.perMaterial) {
            return SwingProfile.DEFAULT;
        }
        SwingProfile exact = BY_ITEM.get(path);
        if (exact != null) {
            return exact;
        }
        for (Map.Entry<String, SwingProfile> entry : BY_MATERIAL.entrySet()) {
            if (path.startsWith(entry.getKey())) {
                return entry.getValue();
            }
        }
        return SwingProfile.DEFAULT;
    }

    /**
     * Stands in for vanilla's {@code swingArm}, which is
     * {@code apply(matrices, progress, side, SwingProfile.VANILLA)} exactly.
     */
    public static void apply(MatrixStack matrices, float swingProgress, int side, SwingProfile profile) {
        float progress = MathHelper.clamp(swingProgress, 0.0F, 1.0F);
        // A heavier blade spends longer in the windup and then covers the rest in a rush. Same
        // total duration, different distribution.
        float warped = profile.weight() <= 0.0F
                ? progress
                : (float) Math.pow(progress, 1.0 + profile.weight() * 0.8F);
        float arc = profile.arc();

        float root = MathHelper.sqrt(warped);
        float swayX = -0.4F * arc * MathHelper.sin(root * MathHelper.PI);
        float swayY = 0.2F * arc * MathHelper.sin(root * MathHelper.TAU);
        float swayZ = -0.2F * arc * MathHelper.sin(warped * MathHelper.PI);
        matrices.translate(side * swayX, swayY, swayZ);

        float snap = MathHelper.sin(warped * warped * MathHelper.PI);
        float sweep = MathHelper.sin(root * MathHelper.PI);
        matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(side * (45.0F + snap * -20.0F * arc)));
        matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(side * sweep * -20.0F * arc));
        matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(sweep * -80.0F * arc));

        // The follow through: past the strike the blade rocks back a little and settles.
        if (profile.settle() > 0.0F && warped > 0.55F) {
            float after = (warped - 0.55F) / 0.45F;
            matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(
                    MathHelper.sin(after * MathHelper.PI) * profile.settle()));
        }

        matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(side * -45.0F));
    }
}
