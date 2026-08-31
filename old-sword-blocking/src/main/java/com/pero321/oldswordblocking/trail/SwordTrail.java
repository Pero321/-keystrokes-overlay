package com.pero321.oldswordblocking.trail;

import com.pero321.oldswordblocking.config.ModConfig;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.item.ItemStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.MathHelper;
import org.joml.Matrix4f;
import org.joml.Vector3f;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

/**
 * The streak that follows the blade through a swing.
 *
 * <p>Every rendered frame the blade's hilt and tip are transformed by the same equip and swing
 * offsets vanilla uses, and pushed into a short ring buffer. The streak is the ribbon stitched
 * between consecutive frames, its oldest end transparent. The samples are relative to the hand
 * stack, so they are submitted through that same stack and land exactly where the blade was.
 */
public final class SwordTrail {

    private static final Identifier TEXTURE = Identifier.of("oldswordblocking", "textures/trail.png");
    private static final RenderLayer LAYER = RenderLayers.entityTranslucentEmissiveNoOutline(TEXTURE);
    /** Full block and sky light: the streak glows on its own rather than picking up the world's. */
    private static final int FULL_BRIGHT = 0xF000F0;

    /** Each entry is one frame: the hilt end and the tip end of the blade. */
    private static final Deque<Ribbon.Segment> SAMPLES = new ArrayDeque<>();

    private SwordTrail() {
    }

    public static void clear() {
        SAMPLES.clear();
    }

    /**
     * Record where the blade is this frame. {@code handToBlade} is the equip and swing transform;
     * {@code side} is 1 for a right handed player and -1 for a left handed one, mirroring the
     * offsets the same way vanilla's left hand display transform mirrors the model.
     */
    public static void sample(Matrix4f handToBlade, int side, ModConfig.TrailConfig config) {
        SAMPLES.addLast(new Ribbon.Segment(
                handToBlade.transformPosition(new Vector3f(side * config.nearX, config.nearY, config.nearZ)),
                handToBlade.transformPosition(new Vector3f(side * config.farX, config.farY, config.farZ))));
        trimTo(config.samples);
    }

    /** Drop the oldest frame, so the streak melts away instead of vanishing when the swing ends. */
    public static void decay() {
        if (!SAMPLES.isEmpty()) {
            SAMPLES.removeFirst();
        }
    }

    public static boolean isEmpty() {
        return SAMPLES.size() < 2;
    }

    public static void submit(OrderedRenderCommandQueue queue, MatrixStack handSpace, ItemStack stack,
                              ModConfig.TrailConfig config) {
        if (isEmpty()) {
            return;
        }
        List<Ribbon.Segment> path = new ArrayList<>(SAMPLES);
        int rgb = TrailPalette.colorFor(stack, config);
        int red = (rgb >> 16) & 0xFF;
        int green = (rgb >> 8) & 0xFF;
        int blue = rgb & 0xFF;
        float peak = MathHelper.clamp(config.opacity, 0.0F, 1.0F);
        int smoothing = config.smoothing;

        queue.submitCustom(handSpace, LAYER, (entry, consumer) ->
                Ribbon.emit(consumer, entry, path, red, green, blue, peak, smoothing));
    }

    private static void trimTo(int max) {
        while (SAMPLES.size() > Math.max(2, max)) {
            SAMPLES.removeFirst();
        }
    }
}
