package com.pero321.oldswordblocking.mixin;

import com.pero321.oldswordblocking.client.BlockingState;
import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
import com.pero321.oldswordblocking.swing.SwingAnimations;
import com.pero321.oldswordblocking.swing.SwingProfile;
import com.pero321.oldswordblocking.trail.SwordTrail;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.AbstractClientPlayerEntity;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.render.item.HeldItemRenderer;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.ItemDisplayContext;
import net.minecraft.item.ItemStack;
import net.minecraft.util.Arm;
import net.minecraft.util.Hand;
import net.minecraft.util.SwingAnimationType;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Everything this mod does to the item in your hand: the pre-1.9 block stance, the weighted swing,
 * and the streak that follows the blade.
 *
 * <p>The block pose is not invented. Vanilla still carries it: an item whose {@code UseAction} is
 * {@code BLOCK} and which is not a shield gets exactly that transform here — the modern descendant
 * of 1.8's {@code ItemRenderer#doBlockTransformations}. Swords simply never reach that branch any
 * more, so this takes it for them.
 *
 * <p>When it takes over it rebuilds vanilla's own plain path — equip offset, swing, then vanilla's
 * item renderer — so nothing about how the item is drawn is reimplemented.
 */
@Mixin(HeldItemRenderer.class)
public abstract class HeldItemRendererMixin {

    @Shadow
    public abstract void renderItem(LivingEntity entity, ItemStack stack, ItemDisplayContext renderMode,
                                    MatrixStack matrices, OrderedRenderCommandQueue queue, int light);

    @Shadow
    protected abstract void applyEquipOffset(MatrixStack matrices, Arm arm, float equipProgress);

    @Shadow
    protected abstract void swingArm(float swingProgress, MatrixStack matrices, int side, Arm arm);

    @Inject(method = "renderFirstPersonItem", at = @At("HEAD"), cancellable = true)
    private void oldswordblocking$renderHeldItem(AbstractClientPlayerEntity player, float tickProgress, float pitch,
                                                 Hand hand, float swingProgress, ItemStack item, float equipProgress,
                                                 MatrixStack matrices, OrderedRenderCommandQueue queue, int light,
                                                 CallbackInfo ci) {
        ModConfig config = ConfigManager.get();
        if (hand != BlockingState.BLOCKING_HAND || player != MinecraftClient.getInstance().player) {
            return;
        }
        if (!config.enabled || item.isEmpty() || !BlockingState.isBlockingItem(item)) {
            SwordTrail.clear();
            return;
        }

        Arm arm = player.getMainArm();
        int side = arm == Arm.RIGHT ? 1 : -1;

        float blockProgress = config.firstPerson ? BlockingState.getProgress(tickProgress) : 0.0F;
        SwingProfile profile = oldswordblocking$swingProfile(player, item, swingProgress, config);

        oldswordblocking$updateTrail(swingProgress, equipProgress, arm, side, profile, item, matrices, queue, config);

        boolean swinging = swingProgress > 0.0F && (blockProgress <= 0.0F || config.allowWhileSwinging);
        if (blockProgress <= 0.0F && profile == null) {
            // Nothing to change about this frame: let vanilla draw it.
            return;
        }

        matrices.push();
        this.applyEquipOffset(matrices, arm, equipProgress);
        if (swinging) {
            if (profile != null) {
                SwingAnimations.apply(matrices, swingProgress, side, profile);
            } else {
                this.swingArm(swingProgress, matrices, side, arm);
            }
        }
        if (blockProgress > 0.0F) {
            oldswordblocking$applyBlockPose(matrices, side, blockProgress, config);
        }

        this.renderItem(player, item,
                arm == Arm.RIGHT ? ItemDisplayContext.FIRST_PERSON_RIGHT_HAND : ItemDisplayContext.FIRST_PERSON_LEFT_HAND,
                matrices, queue, light);

        matrices.pop();
        ci.cancel();
    }

    /** The old block pose, eased in and out by {@code progress} so it does not snap. */
    @Unique
    private void oldswordblocking$applyBlockPose(MatrixStack matrices, int side, float progress, ModConfig config) {
        matrices.translate(side * config.offsetX * progress, config.offsetY * progress, config.offsetZ * progress);
        matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(config.rotationX * progress));
        matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(side * config.rotationY * progress));
        matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(side * config.rotationZ * progress));
        if (config.scale != 1.0F) {
            float extra = MathHelper.lerp(progress, 1.0F, config.scale);
            matrices.scale(extra, extra, extra);
        }
    }

    /**
     * The weighted swing for this blade, or null when vanilla's should be left alone — the mod is
     * off, the arm is still, or the item has a use or a swing style this does not own.
     */
    @Unique
    private SwingProfile oldswordblocking$swingProfile(AbstractClientPlayerEntity player, ItemStack item,
                                                       float swingProgress, ModConfig config) {
        if (!config.swing.enabled || swingProgress <= 0.0F) {
            return null;
        }
        if (player.isUsingItem() || player.isUsingRiptide()) {
            return null;
        }
        if (item.getSwingAnimation().type() != SwingAnimationType.WHACK) {
            return null;
        }
        return SwingAnimations.profileFor(item, config.swing);
    }

    /**
     * Feeds the blade's position to {@link SwordTrail} once per rendered frame, through whichever
     * swing is actually being drawn, so the streak always tracks the blade.
     */
    @Unique
    private void oldswordblocking$updateTrail(float swingProgress, float equipProgress, Arm arm, int side,
                                              SwingProfile profile, ItemStack item, MatrixStack matrices,
                                              OrderedRenderCommandQueue queue, ModConfig config) {
        if (!config.trail.enabled) {
            SwordTrail.clear();
            return;
        }

        if (swingProgress > 0.0F) {
            // A scratch stack rooted at identity, so the sample comes out relative to the hand
            // stack rather than in whatever space that stack happens to sit in this frame.
            MatrixStack delta = new MatrixStack();
            this.applyEquipOffset(delta, arm, equipProgress);
            if (profile != null) {
                SwingAnimations.apply(delta, swingProgress, side, profile);
            } else {
                this.swingArm(swingProgress, delta, side, arm);
            }
            SwordTrail.sample(delta.peek().getPositionMatrix(), side, config.trail);
        } else {
            SwordTrail.decay();
        }

        SwordTrail.submit(queue, matrices, item, config.trail);
    }
}
