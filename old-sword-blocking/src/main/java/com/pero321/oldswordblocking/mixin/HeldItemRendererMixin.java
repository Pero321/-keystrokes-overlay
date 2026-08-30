package com.pero321.oldswordblocking.mixin;

import com.pero321.oldswordblocking.client.BlockingState;
import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
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
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Draws the held sword in the pre-1.9 block stance.
 *
 * <p>No new maths is invented here. Vanilla still carries the old pose: an item whose
 * {@code UseAction} is {@code BLOCK} and which is not a shield gets exactly the transform below
 * inside {@link HeldItemRenderer} — it is the modern descendant of 1.8's
 * {@code ItemRenderer#doBlockTransformations}. Swords simply never reach that branch any more,
 * because since 1.9 right clicking a sword does nothing at all. So we take the branch for them.
 *
 * <p>We reuse vanilla's own {@code applyEquipOffset} and {@code swingArm} so the hand sits and
 * swings precisely where it normally would, then hand the stack back to vanilla's item renderer.
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
    private void oldswordblocking$renderBlockPose(AbstractClientPlayerEntity player, float tickProgress, float pitch,
                                                  Hand hand, float swingProgress, ItemStack item, float equipProgress,
                                                  MatrixStack matrices, OrderedRenderCommandQueue queue, int light,
                                                  CallbackInfo ci) {
        ModConfig config = ConfigManager.get();
        boolean localMainHand = hand == BlockingState.BLOCKING_HAND
                && player == MinecraftClient.getInstance().player;
        if (localMainHand) {
            oldswordblocking$updateTrail(player, swingProgress, item, equipProgress, matrices, queue);
        }

        if (!config.enabled || !config.firstPerson) {
            return;
        }
        if (!localMainHand) {
            return;
        }
        if (item.isEmpty() || !BlockingState.isBlockingItem(item)) {
            return;
        }

        float progress = BlockingState.getProgress(tickProgress);
        if (progress <= 0.0F) {
            return;
        }

        Arm arm = player.getMainArm();
        int side = arm == Arm.RIGHT ? 1 : -1;

        matrices.push();
        this.applyEquipOffset(matrices, arm, equipProgress);

        // 1.8 kept swinging while you blocked; vanilla's own BLOCK branch does not. Your call.
        if (config.allowWhileSwinging) {
            this.swingArm(swingProgress, matrices, side, arm);
        }

        // The old block pose, eased in and out by `progress` so it does not snap.
        matrices.translate(side * config.offsetX * progress, config.offsetY * progress, config.offsetZ * progress);
        matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(config.rotationX * progress));
        matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(side * config.rotationY * progress));
        matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(side * config.rotationZ * progress));
        if (config.scale != 1.0F) {
            float extra = MathHelper.lerp(progress, 1.0F, config.scale);
            matrices.scale(extra, extra, extra);
        }

        this.renderItem(player, item,
                arm == Arm.RIGHT ? ItemDisplayContext.FIRST_PERSON_RIGHT_HAND : ItemDisplayContext.FIRST_PERSON_LEFT_HAND,
                matrices, queue, light);

        matrices.pop();
        ci.cancel();
    }

    /**
     * Feeds the blade's position to {@link SwordTrail} once per rendered frame. The sample is taken
     * from vanilla's own equip and swing transforms on a pushed copy of the stack, so the streak
     * tracks the blade exactly and the real render is left untouched.
     */
    @Unique
    private void oldswordblocking$updateTrail(AbstractClientPlayerEntity player, float swingProgress,
                                              ItemStack item, float equipProgress, MatrixStack matrices,
                                              OrderedRenderCommandQueue queue) {
        ModConfig config = ConfigManager.get();
        if (!config.enabled || !config.trail.enabled || item.isEmpty() || !BlockingState.isBlockingItem(item)) {
            SwordTrail.clear();
            return;
        }

        if (swingProgress > 0.0F) {
            Arm arm = player.getMainArm();
            int side = arm == Arm.RIGHT ? 1 : -1;
            // A scratch stack rooted at identity, so the sample comes out relative to the hand
            // stack rather than in whatever space that stack happens to sit in this frame.
            MatrixStack delta = new MatrixStack();
            this.applyEquipOffset(delta, arm, equipProgress);
            this.swingArm(swingProgress, delta, side, arm);
            SwordTrail.sample(delta.peek().getPositionMatrix(), side, config.trail);
        } else {
            SwordTrail.decay();
        }

        SwordTrail.submit(queue, matrices, config.trail);
    }
}
