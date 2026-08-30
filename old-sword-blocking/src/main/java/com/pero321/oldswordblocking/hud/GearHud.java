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
 * A compact strip of your armour and held tools: the icon, a durability bar under it, and a
 * pulsing red badge on anything about to break. Nothing else — the bars carry the reading, so the
 * strip stays small enough to ignore until it matters.
 *
 * <p>A piece that drops into the danger zone also gets one line in chat naming it, so a helmet
 * never quietly pops mid fight.
 */
public class GearHud implements HudElement {

    private static final EquipmentSlot[] SLOTS = {
            EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET,
            EquipmentSlot.MAINHAND, EquipmentSlot.OFFHAND
    };

    private static final int ICON = 16;
    private static final int GAP = 2;
    private static final int BAR_GAP = 1;
    private static final int BAR_HEIGHT = 2;
    private static final int BAR_BACKGROUND = 0xFF141414;

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
                if (previous == null || !ItemStack.areItemsEqual(previous, stack)
                        || percentLeft(stack) > config.warnBelowPercent) {
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
        /*
         * Never draw behind an open screen. Beyond being pointless, it matters: since 1.21.9 every
         * item drawn in a frame takes a slot in a GPU atlas whose size is capped by the device's
         * maximum texture size. A full creative tab can already fill that atlas on a device with a
         * small cap, and anything that does not fit renders as a black square. Adding six more
         * items behind the screen is exactly the wrong moment to spend those slots.
         */
        if (client.currentScreen != null) {
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

        HudAnchor anchor = HudAnchor.parse(config.gearAnchor);
        boolean vertical = !"HORIZONTAL".equalsIgnoreCase(config.gearLayout);

        int labelWidth = 0;
        if (config.showDurabilityNumbers) {
            for (ItemStack stack : shown) {
                labelWidth = Math.max(labelWidth, client.textRenderer.getWidth(label(stack, config)));
            }
        }

        int rowHeight = ICON + (config.showBar ? BAR_GAP + BAR_HEIGHT : 0);
        int width;
        int height;
        if (vertical) {
            width = ICON + (labelWidth > 0 ? labelWidth + GAP : 0);
            height = shown.size() * (rowHeight + GAP) - GAP;
        } else {
            int cell = Math.max(ICON, labelWidth) + GAP;
            width = shown.size() * cell - GAP;
            height = rowHeight + (labelWidth > 0 ? BAR_GAP + client.textRenderer.fontHeight : 0);
        }

        int left = anchor.x(context, width, config.gearOffsetX + (config.background ? HudTheme.PADDING : 0));
        int top = anchor.y(context, height, config.gearOffsetY + (config.background ? HudTheme.PADDING : 0));

        if (config.background) {
            HudTheme.panel(context, left, top, width, height);
        }

        for (int i = 0; i < shown.size(); i++) {
            ItemStack stack = shown.get(i);
            if (vertical) {
                int y = top + i * (rowHeight + GAP);
                // On the right the icons hug the edge and the numbers sit inside them, and the
                // other way round on the left, so the column always reads towards the screen.
                int iconX = anchor.isRightAligned() ? left + width - ICON : left;
                int labelX = anchor.isRightAligned() ? left : left + ICON + GAP;
                drawPiece(context, client, stack, iconX, y, config);
                if (labelWidth > 0) {
                    String text = label(stack, config);
                    int x = anchor.isRightAligned() ? labelX + labelWidth - client.textRenderer.getWidth(text) : labelX;
                    context.drawTextWithShadow(client.textRenderer, text, x,
                            y + (ICON - client.textRenderer.fontHeight) / 2 + 1, numberColor(stack, config));
                }
            } else {
                int cell = Math.max(ICON, labelWidth) + GAP;
                int x = left + i * cell;
                drawPiece(context, client, stack, x + (Math.max(ICON, labelWidth) - ICON) / 2, top, config);
                if (labelWidth > 0) {
                    String text = label(stack, config);
                    int labelX = x + (Math.max(ICON, labelWidth) - client.textRenderer.getWidth(text)) / 2;
                    context.drawTextWithShadow(client.textRenderer, text, labelX,
                            top + rowHeight + BAR_GAP, numberColor(stack, config));
                }
            }
        }
    }

    private void drawPiece(DrawContext context, MinecraftClient client, ItemStack stack,
                           int x, int top, ModConfig.HudConfig config) {
        int percent = percentLeft(stack);
        boolean low = percent <= config.warnBelowPercent;

        context.drawItem(stack, x, top);

        if (config.showBar) {
            int barY = top + ICON + BAR_GAP;
            context.fill(x, barY, x + ICON, barY + BAR_HEIGHT, BAR_BACKGROUND);
            int filled = Math.round(ICON * percent / 100.0F);
            if (filled > 0) {
                context.fill(x, barY, x + filled, barY + BAR_HEIGHT, HudTheme.forPercent(percent));
            }
        }

        if (low) {
            // A badge in the icon's corner: a slow pulse, so it reads as a warning rather than as
            // part of the furniture, without stealing a whole row of height.
            float pulse = 0.5F + 0.5F * MathHelper.sin(
                    (client.player.age + client.getRenderTickCounter().getTickProgress(false)) * 0.3F);
            int alpha = MathHelper.clamp(90 + (int) (pulse * 165.0F), 0, 255);
            context.drawTextWithShadow(client.textRenderer, "!", x + ICON - 3, top,
                    (alpha << 24) | (HudTheme.BAD & 0x00FFFFFF));
        }
    }

    /** The durability actually left, which is what you want to know, not how broken it is. */
    private static String label(ItemStack stack, ModConfig.HudConfig config) {
        int left = stack.getMaxDamage() - stack.getDamage();
        return config.showMaxDurability ? left + "/" + stack.getMaxDamage() : String.valueOf(left);
    }

    private static int numberColor(ItemStack stack, ModConfig.HudConfig config) {
        int percent = percentLeft(stack);
        return percent <= config.warnBelowPercent ? HudTheme.BAD : HudTheme.forPercent(percent);
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
}
