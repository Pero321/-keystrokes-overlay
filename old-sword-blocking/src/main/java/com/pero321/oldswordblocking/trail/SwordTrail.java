package com.pero321.oldswordblocking.trail;

import com.pero321.oldswordblocking.config.ModConfig;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.VertexConsumer;
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
    private static final Deque<Segment> SAMPLES = new ArrayDeque<>();

    private record Segment(Vector3f near, Vector3f far) {
    }

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
        SAMPLES.addLast(new Segment(
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
        List<Segment> segments = new ArrayList<>(SAMPLES);
        int rgb = TrailPalette.colorFor(stack, config);
        int red = (rgb >> 16) & 0xFF;
        int green = (rgb >> 8) & 0xFF;
        int blue = rgb & 0xFF;
        float peak = MathHelper.clamp(config.opacity, 0.0F, 1.0F);

        int count = segments.size();
        queue.submitCustom(handSpace, LAYER, (entry, consumer) -> {
            for (int i = 0; i < count - 1; i++) {
                Vector3f nearFrom = taperedNear(segments.get(i), i, count);
                Vector3f nearTo = taperedNear(segments.get(i + 1), i + 1, count);
                Vector3f farFrom = segments.get(i).far();
                Vector3f farTo = segments.get(i + 1).far();
                int alphaFrom = alphaAt(i, count, peak);
                int alphaTo = alphaAt(i + 1, count, peak);
                // Both windings, so the ribbon is visible from either side of the swing.
                quad(consumer, entry, nearFrom, farFrom, farTo, nearTo, red, green, blue, alphaFrom, alphaTo);
                quad(consumer, entry, nearTo, farTo, farFrom, nearFrom, red, green, blue, alphaTo, alphaFrom);
            }
        });
    }

    /**
     * Pulls the hilt end of an older sample toward the tip, so the ribbon narrows into its tail
     * instead of ending in a blunt rectangle.
     */
    private static Vector3f taperedNear(Segment segment, int index, int count) {
        float age = count <= 1 ? 1.0F : (float) index / (count - 1);
        float width = 0.25F + 0.75F * age;
        return new Vector3f(segment.far()).lerp(segment.near(), width);
    }

    private static void quad(VertexConsumer consumer, MatrixStack.Entry entry,
                             Vector3f a, Vector3f b, Vector3f c, Vector3f d,
                             int red, int green, int blue, int alphaAb, int alphaCd) {
        vertex(consumer, entry, a, 0.0F, 0.0F, red, green, blue, alphaAb);
        vertex(consumer, entry, b, 1.0F, 0.0F, red, green, blue, alphaAb);
        vertex(consumer, entry, c, 1.0F, 1.0F, red, green, blue, alphaCd);
        vertex(consumer, entry, d, 0.0F, 1.0F, red, green, blue, alphaCd);
    }

    private static void vertex(VertexConsumer consumer, MatrixStack.Entry entry, Vector3f position,
                               float u, float v, int red, int green, int blue, int alpha) {
        consumer.vertex(entry, position.x, position.y, position.z)
                .color(red, green, blue, alpha)
                .texture(u, v)
                .overlay(OverlayTexture.DEFAULT_UV)
                .light(FULL_BRIGHT)
                .normal(entry, 0.0F, 1.0F, 0.0F);
    }

    /** Oldest sample fully transparent, newest at the configured opacity. */
    private static int alphaAt(int index, int count, float peak) {
        float fraction = count <= 1 ? 1.0F : (float) index / (count - 1);
        return MathHelper.clamp(Math.round(fraction * fraction * peak * 255.0F), 0, 255);
    }

    private static void trimTo(int max) {
        while (SAMPLES.size() > Math.max(2, max)) {
            SAMPLES.removeFirst();
        }
    }

}
