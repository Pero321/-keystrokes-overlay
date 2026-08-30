package com.pero321.oldswordblocking.hud;

import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.render.RenderTickCounter;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.item.ItemStack;
import net.minecraft.text.Text;
import net.minecraft.util.math.MathHelper;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * A strip of your armour and held tools, each with the durability left under it. Anything that
 * drops into the danger zone gets a red exclamation mark over it and, once, a line in chat naming
 * the piece — so a helmet never quietly pops mid fight.
 */
public class GearHud implements HudElement {

    private static final EquipmentSlot[] SLOTS = {
            EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET,
            EquipmentSlot.MAINHAND, EquipmentSlot.OFFHAND
    };

    private static final int ICON = 16;
    private static final int GAP = 4;
    private static final int BAR_HEIGHT = 2;
    private static final int BAR_GAP = 1;
    /** Room above the icons for the exclamation mark. */
    private static final int MARK_HEIGHT = 9;

    private static final int BAR_BACKGROUND = 0xFF000000;
    private static final int TEXT_COLOR = 0xFFDDDDDD;
    private static final int WARNING_COLOR = 0xFFFF5555;

    /** Whether we have already spoken up about the item currently in each slot. */
    private final Map<EquipmentSlot, Boolean> warned = new EnumMap<>(EquipmentSlot.class);
    private final Map<EquipmentSlot, ItemStack> lastSeen = new EnumMap<>(EquipmentSlot.class);

    /**
     * Chat warnings live on the tick, not the frame, so the message fires once rather than once
     * per rendered frame.
     */
    public void tick(MinecraftClient client) {
        ModConfig.HudConfig config = ConfigManager.get().hud;
        ClientPlayerEntity player = client.player;
        if (player == null) {
            this.warned.clear();
            this.lastSeen.clear();
            return;
        }

        for (EquipmentSlot slot : SLOTS) {
            ItemStack stack = player.getEquippedStack(slot);

            // A swap or a repair earns the piece a fresh warning later on.
            ItemStack previous = this.lastSeen.get(slot);
            if (previous == null || !ItemStack.areEqual(previous, stack)) {
                this.lastSeen.put(slot, stack.copy());
                if (previous == null || !ItemStack.areItemsEqual(previous, stack) || percentLeft(stack) > config.warnBelowPercent) {
                    this.warned.put(slot, false);
                }
            }

            if (!isTracked(stack) || percentLeft(stack) > config.warnBelowPercent) {
                continue;
            }
            if (Boolean.TRUE.equals(this.warned.get(slot))) {
                continue;
            }
            this.warned.put(slot, true);
            if (config.warnInChat && ConfigManager.get().enabled) {
                player.sendMessage(Text.translatable("text.oldswordblocking.gear_warning",
                        stack.getName(), percentLeft(stack)), false);
            }
        }
    }

    @Override
    public void render(DrawContext context, RenderTickCounter tickCounter) {
        MinecraftClient client = MinecraftClient.getInstance();
        ModConfig.HudConfig config = ConfigManager.get().hud;

        if (!ConfigManager.get().enabled || !config.showGear
                || client.player == null || client.options.hudHidden) {
            return;
        }

        List<ItemStack> shown = new ArrayList<>(SLOTS.length);
        for (EquipmentSlot slot : SLOTS) {
            if (slot == EquipmentSlot.OFFHAND && !config.includeOffHand) {
                continue;
            }
            ItemStack stack = client.player.getEquippedStack(slot);
            if (!isTracked(stack)) {
                continue;
            }
            if (config.onlyDamagedGear && stack.getDamage() == 0) {
                continue;
            }
            shown.add(stack);
        }
        if (shown.isEmpty()) {
            return;
        }

        // Cells are as wide as the widest "100%" style label, so the numbers never touch.
        int content = ICON;
        for (ItemStack stack : shown) {
            content = Math.max(content, client.textRenderer.getWidth(label(stack)));
        }
        int cellWidth = content + GAP;
        int width = shown.size() * cellWidth - GAP;
        int height = MARK_HEIGHT + ICON + BAR_GAP + BAR_HEIGHT + BAR_GAP + client.textRenderer.fontHeight;

        HudAnchor anchor = HudAnchor.parse(config.gearAnchor);
        int left = anchor.x(context, width, config.gearOffsetX);
        int top = anchor.y(context, height, config.gearOffsetY);

        for (int i = 0; i < shown.size(); i++) {
            drawPiece(context, client, shown.get(i), left + i * cellWidth, content, top, config);
        }
    }

    private void drawPiece(DrawContext context, MinecraftClient client, ItemStack stack,
                           int cellX, int content, int top, ModConfig.HudConfig config) {
        int percent = percentLeft(stack);
        boolean low = percent <= config.warnBelowPercent;

        int x = cellX + (content - ICON) / 2;
        int iconY = top + MARK_HEIGHT;
        context.drawItem(stack, x, iconY);

        int barY = iconY + ICON + BAR_GAP;
        int barColor = durabilityColor(percent);
        context.fill(x - 1, barY - 1, x + ICON + 1, barY + BAR_HEIGHT + 1, BAR_BACKGROUND);
        int filled = Math.round(ICON * percent / 100.0F);
        if (filled > 0) {
            context.fill(x, barY, x + filled, barY + BAR_HEIGHT, barColor);
        }

        String label = label(stack);
        int labelX = cellX + (content - client.textRenderer.getWidth(label)) / 2;
        context.drawTextWithShadow(client.textRenderer, label, labelX, barY + BAR_HEIGHT + BAR_GAP + 1,
                low ? WARNING_COLOR : TEXT_COLOR);

        if (low) {
            // A slow pulse, so it reads as a warning rather than as part of the furniture.
            float pulse = 0.55F + 0.45F * MathHelper.sin((client.player.age + client.getRenderTickCounter()
                    .getTickProgress(false)) * 0.35F);
            int alpha = MathHelper.clamp((int) (pulse * 255.0F), 0, 255);
            int mark = (alpha << 24) | (WARNING_COLOR & 0x00FFFFFF);
            int markX = cellX + (content - client.textRenderer.getWidth("!")) / 2;
            context.drawTextWithShadow(client.textRenderer, "!", markX, top, mark);
        }
    }

    private static String label(ItemStack stack) {
        return percentLeft(stack) + "%";
    }

    private static boolean isTracked(ItemStack stack) {
        return !stack.isEmpty() && stack.isDamageable() && stack.getMaxDamage() > 0;
    }

    /** 100 for pristine, 0 for one hit from breaking. */
    private static int percentLeft(ItemStack stack) {
        if (!isTracked(stack)) {
            return 100;
        }
        int left = stack.getMaxDamage() - stack.getDamage();
        return MathHelper.clamp(Math.round(left * 100.0F / stack.getMaxDamage()), 0, 100);
    }

    private static int durabilityColor(int percent) {
        // Green above half, through amber, to red at the end. Same reading as the vanilla bar.
        float hue = MathHelper.clamp(percent / 100.0F, 0.0F, 1.0F) / 3.0F;
        return 0xFF000000 | MathHelper.hsvToArgb(hue, 1.0F, 1.0F, 255) & 0x00FFFFFF;
    }
}
