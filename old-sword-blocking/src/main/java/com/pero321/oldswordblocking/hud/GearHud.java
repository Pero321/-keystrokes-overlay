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
 * A compact column of your armour and held tools: the icon and the durability actually left on it,
 * coloured by how much of that there is. Points left, not a percentage — that is the number you act
 * on. Armour and hands are separated by a small gap, so the block reads as two groups at a glance.
 *
 * <p>A piece past the warning threshold gets a pulsing badge, shakes in short bursts, and gets one
 * line in chat naming it, so a helmet never quietly pops mid fight.
 */
public class GearHud implements HudElement {

    private static final EquipmentSlot[] SLOTS = {
            EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET,
            EquipmentSlot.MAINHAND, EquipmentSlot.OFFHAND
    };

    private static final int ICON = 16;
    private static final int GAP = 2;
    /** Extra room between the armour group and the held items. */
    private static final int GROUP_GAP = 5;
    private static final int BAR_GAP = 1;
    private static final int BAR_HEIGHT = 2;
    private static final int BAR_BACKGROUND = 0xFF141414;
    /** How long one shake burst lasts, in ticks. */
    private static final float SHAKE_TICKS = 9.0F;

    private record Piece(ItemStack stack, boolean held) {
    }

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

        List<Piece> shown = new ArrayList<>(SLOTS.length);
        for (EquipmentSlot slot : SLOTS) {
            if (slot == EquipmentSlot.OFFHAND && !config.includeOffHand) {
                continue;
            }
            ItemStack stack = client.player.getEquippedStack(slot);
            if (!isTracked(stack) || (config.onlyDamagedGear && stack.getDamage() == 0)) {
                continue;
            }
            shown.add(new Piece(stack, slot == EquipmentSlot.MAINHAND || slot == EquipmentSlot.OFFHAND));
        }
        if (shown.isEmpty()) {
            return;
        }

        HudAnchor anchor = HudAnchor.parse(config.gearAnchor);
        boolean vertical = !"HORIZONTAL".equalsIgnoreCase(config.gearLayout);

        int labelWidth = 0;
        if (config.showDurabilityNumbers) {
            for (Piece piece : shown) {
                labelWidth = Math.max(labelWidth, client.textRenderer.getWidth(label(piece.stack(), config)));
            }
        }

        int rowHeight = ICON + (config.showBar ? BAR_GAP + BAR_HEIGHT : 0);
        int[] offsets = layout(shown, vertical ? rowHeight : Math.max(ICON, labelWidth), GAP);
        int span = offsets[offsets.length - 1];

        int width;
        int height;
        if (vertical) {
            width = ICON + (labelWidth > 0 ? labelWidth + GAP : 0);
            height = span;
        } else {
            width = span;
            height = rowHeight + (labelWidth > 0 ? BAR_GAP + client.textRenderer.fontHeight : 0);
        }

        float scale = config.scale;
        int screenWidth = Math.round(context.getScaledWindowWidth() / scale);
        int screenHeight = Math.round(context.getScaledWindowHeight() / scale);
        int pad = config.background ? HudTheme.PADDING : 0;
        int left = anchor.x(screenWidth, width, config.gearOffsetX + pad);
        int top = anchor.y(screenHeight, height, config.gearOffsetY + pad);

        context.getMatrices().pushMatrix();
        context.getMatrices().scale(scale, scale);

        if (config.background) {
            HudTheme.panel(context, left, top, width, height);
        }

        for (int i = 0; i < shown.size(); i++) {
            ItemStack stack = shown.get(i).stack();
            if (vertical) {
                int y = top + offsets[i];
                // On the right the icons hug the edge and the numbers sit inside them, and the
                // other way round on the left, so the column always reads towards the screen.
                int iconX = anchor.isRightAligned() ? left + width - ICON : left;
                int labelX = anchor.isRightAligned() ? left : left + ICON + GAP;
                drawPiece(context, client, stack, iconX, y, i, config);
                if (labelWidth > 0) {
                    String text = label(stack, config);
                    int x = anchor.isRightAligned() ? labelX + labelWidth - client.textRenderer.getWidth(text) : labelX;
                    HudTheme.text(context, client.textRenderer, text, x,
                            y + (ICON - client.textRenderer.fontHeight) / 2 + 1,
                            numberColor(stack, config), config.outlineText);
                }
            } else {
                int cellWidth = Math.max(ICON, labelWidth);
                int x = left + offsets[i];
                drawPiece(context, client, stack, x + (cellWidth - ICON) / 2, top, i, config);
                if (labelWidth > 0) {
                    String text = label(stack, config);
                    HudTheme.text(context, client.textRenderer, text,
                            x + (cellWidth - client.textRenderer.getWidth(text)) / 2,
                            top + rowHeight + BAR_GAP, numberColor(stack, config), config.outlineText);
                }
            }
        }

        context.getMatrices().popMatrix();
    }

    /**
     * Start offset for each piece plus, in the last slot, the total span. Held items get an extra
     * gap in front of them so armour and hands read as two groups.
     */
    private static int[] layout(List<Piece> pieces, int step, int gap) {
        int[] offsets = new int[pieces.size() + 1];
        int cursor = 0;
        for (int i = 0; i < pieces.size(); i++) {
            if (i > 0) {
                cursor += gap + (pieces.get(i).held() && !pieces.get(i - 1).held() ? GROUP_GAP : 0);
            }
            offsets[i] = cursor;
            cursor += step;
        }
        offsets[pieces.size()] = cursor;
        return offsets;
    }

    private void drawPiece(DrawContext context, MinecraftClient client, ItemStack stack,
                           int x, int top, int index, ModConfig.HudConfig config) {
        int percent = percentLeft(stack);
        boolean low = percent <= config.warnBelowPercent;

        // A piece about to go shakes in bursts. The icon moves, the number beside it does not, so
        // the movement catches the eye without making the figure hard to read.
        int shakeX = 0;
        int shakeY = 0;
        if (low && config.shakeWhenLow) {
            float time = client.player.age + client.getRenderTickCounter().getTickProgress(false);
            // Each piece runs on its own clock, so a row of them does not judder in lockstep.
            time += index * 7.0F;
            float urgency = MathHelper.clamp(
                    1.0F - (float) percent / Math.max(1, config.warnBelowPercent), 0.0F, 1.0F);
            float period = 50.0F - 30.0F * urgency;
            float phase = time % period;
            if (phase < SHAKE_TICKS) {
                float envelope = 1.0F - phase / SHAKE_TICKS;
                float amplitude = (1.0F + urgency) * envelope;
                shakeX = Math.round(MathHelper.sin(time * 2.3F) * amplitude);
                shakeY = Math.round(MathHelper.sin(time * 3.7F) * amplitude * 0.7F);
            }
        }

        context.drawItem(stack, x + shakeX, top + shakeY);

        if (config.showBar) {
            int barY = top + ICON + BAR_GAP;
            context.fill(x, barY, x + ICON, barY + BAR_HEIGHT, BAR_BACKGROUND);
            int filled = Math.round(ICON * percent / 100.0F);
            if (filled > 0) {
                context.fill(x, barY, x + filled, barY + BAR_HEIGHT, HudTheme.forPercent(percent));
            }
        }

        if (low) {
            float pulse = 0.5F + 0.5F * MathHelper.sin(
                    (client.player.age + client.getRenderTickCounter().getTickProgress(false)) * 0.3F);
            int alpha = MathHelper.clamp(90 + (int) (pulse * 165.0F), 0, 255);
            HudTheme.text(context, client.textRenderer, "!", x + ICON - 3 + shakeX, top + shakeY,
                    (alpha << 24) | (HudTheme.BAD & 0x00FFFFFF), config.outlineText);
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
