package com.pero321.oldswordblocking.mixin;

import com.pero321.oldswordblocking.client.BlockingState;
import com.pero321.oldswordblocking.config.ConfigManager;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.entity.PlayerEntityRenderer;
import net.minecraft.client.render.entity.model.BipedEntityModel;
import net.minecraft.entity.PlayerLikeEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.util.Hand;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Third person half of the illusion: your own body raises the arm the way a shield block does.
 * Only ever applied to the local player, so other people on the server are untouched.
 */
@Mixin(PlayerEntityRenderer.class)
public class PlayerEntityRendererMixin {

    @Inject(method = "getArmPose(Lnet/minecraft/entity/PlayerLikeEntity;Lnet/minecraft/item/ItemStack;Lnet/minecraft/util/Hand;)Lnet/minecraft/client/render/entity/model/BipedEntityModel$ArmPose;",
            at = @At("RETURN"), cancellable = true)
    private static void oldswordblocking$blockArmPose(PlayerLikeEntity player, ItemStack stack, Hand hand,
                                                      CallbackInfoReturnable<BipedEntityModel.ArmPose> cir) {
        if (!ConfigManager.get().enabled || !ConfigManager.get().thirdPerson) {
            return;
        }
        if (hand != BlockingState.BLOCKING_HAND || player != MinecraftClient.getInstance().player) {
            return;
        }
        // Only take over the plain "holding an item" pose; never stomp a bow, crossbow or spyglass.
        if (cir.getReturnValue() != BipedEntityModel.ArmPose.ITEM) {
            return;
        }
        if (BlockingState.getProgress(1.0F) < 0.5F || !BlockingState.isBlockingItem(stack)) {
            return;
        }
        cir.setReturnValue(BipedEntityModel.ArmPose.BLOCK);
    }
}
