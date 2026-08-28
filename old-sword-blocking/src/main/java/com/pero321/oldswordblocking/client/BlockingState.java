package com.pero321.oldswordblocking.client;

import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.item.BlockItem;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.tag.ItemTags;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.MathHelper;

/**
 * The whole "am I blocking" decision lives here, and it lives only on this client:
 * nothing is sent to the server, no packet changes, no gameplay effect. Purely a pose.
 */
public final class BlockingState {

    /** Hand the pose is drawn on. 1.8 only ever blocked with the main hand. */
    public static final Hand BLOCKING_HAND = Hand.MAIN_HAND;

    private static boolean active;
    private static float progress;
    private static float previousProgress;

    private BlockingState() {
    }

    public static void tick(MinecraftClient client) {
        previousProgress = progress;
        active = shouldBlock(client);

        int ticks = ConfigManager.get().transitionTicks;
        float step = ticks <= 0 ? 1.0F : 1.0F / ticks;
        progress = MathHelper.clamp(progress + (active ? step : -step), 0.0F, 1.0F);
    }

    /** 0 = normal pose, 1 = full block pose, smoothly interpolated between client ticks. */
    public static float getProgress(float tickDelta) {
        return MathHelper.lerp(MathHelper.clamp(tickDelta, 0.0F, 1.0F), previousProgress, progress);
    }

    public static boolean isActive() {
        return active;
    }

    public static void reset() {
        active = false;
        progress = 0.0F;
        previousProgress = 0.0F;
    }

    public static boolean isBlockingItem(ItemStack stack) {
        if (stack.isEmpty()) {
            return false;
        }
        ModConfig config = ConfigManager.get();
        if (config.allowAnyItem) {
            return true;
        }
        if (config.allowSwords && stack.isIn(ItemTags.SWORDS)) {
            return true;
        }
        if (config.allowAxes && stack.isIn(ItemTags.AXES)) {
            return true;
        }
        return !config.extraItems.isEmpty()
                && config.extraItems.contains(Registries.ITEM.getId(stack.getItem()).toString());
    }

    private static boolean shouldBlock(MinecraftClient client) {
        ModConfig config = ConfigManager.get();
        if (!config.enabled) {
            return false;
        }

        ClientPlayerEntity player = client.player;
        if (player == null || client.world == null) {
            return false;
        }
        // A chat box or an open chest swallows the right click; do not pose behind a screen.
        if (client.currentScreen != null || !client.isWindowFocused()) {
            return false;
        }
        if (player.isSpectator()) {
            return false;
        }
        // Eating, drawing a bow, raising a shield: vanilla owns the hand, leave it alone.
        if (player.isUsingItem()) {
            return false;
        }
        if (!client.options.useKey.isPressed()) {
            return false;
        }
        if (!config.allowWhileSwinging && player.getHandSwingProgress(1.0F) > 0.0F) {
            return false;
        }

        ItemStack main = player.getStackInHand(BLOCKING_HAND);
        if (!isBlockingItem(main)) {
            return false;
        }

        ItemStack offHand = player.getOffHandStack();
        if (!offHand.isEmpty()) {
            if (config.requireEmptyOffhand) {
                return false;
            }
            // Right click is busy stacking blocks from the off hand: that is not a block stance.
            if (config.suppressWhenPlacingFromOffhand
                    && offHand.getItem() instanceof BlockItem
                    && client.crosshairTarget != null
                    && client.crosshairTarget.getType() == HitResult.Type.BLOCK) {
                return false;
            }
        }

        return true;
    }
}
