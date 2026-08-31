package com.pero321.oldswordblocking.trail;

import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.MathHelper;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.List;

/**
 * Turns a run of samples into a fading ribbon.
 *
 * <p>Shared by the sword streak and the projectile streaks: both are the same shape, a strip
 * stitched between successive frames, narrowing and fading into its tail. Samples are smoothed with
 * a Catmull-Rom pass first, so a fast swing reads as a curve rather than a chain of flat facets.
 */
public final class Ribbon {

    /** Full block and sky light: a streak glows on its own rather than picking up the world's. */
    public static final int FULL_BRIGHT = 0xF000F0;

    /** One frame of the ribbon: the two edges of the strip at that moment. */
    public record Segment(Vector3f near, Vector3f far) {
    }

    private Ribbon() {
    }

    /**
     * @param smoothing extra points inserted between each pair of samples; 0 draws them raw
     */
    public static void emit(VertexConsumer consumer, MatrixStack.Entry entry, List<Segment> samples,
                            int red, int green, int blue, float peakAlpha, int smoothing) {
        List<Segment> path = smoothing > 0 && samples.size() >= 2 ? smooth(samples, smoothing) : samples;
        int count = path.size();
        if (count < 2) {
            return;
        }

        for (int i = 0; i < count - 1; i++) {
            Vector3f nearFrom = taperedNear(path.get(i), i, count);
            Vector3f nearTo = taperedNear(path.get(i + 1), i + 1, count);
            Vector3f farFrom = path.get(i).far();
            Vector3f farTo = path.get(i + 1).far();
            int alphaFrom = alphaAt(i, count, peakAlpha);
            int alphaTo = alphaAt(i + 1, count, peakAlpha);
            // Both windings, so the ribbon is visible from either side.
            quad(consumer, entry, nearFrom, farFrom, farTo, nearTo, red, green, blue, alphaFrom, alphaTo);
            quad(consumer, entry, nearTo, farTo, farFrom, nearFrom, red, green, blue, alphaTo, alphaFrom);
        }
    }

    /** Catmull-Rom through both edges of the strip, so the ribbon curves with the motion. */
    private static List<Segment> smooth(List<Segment> samples, int subdivisions) {
        int count = samples.size();
        List<Segment> out = new ArrayList<>(count * (subdivisions + 1));
        for (int i = 0; i < count - 1; i++) {
            Segment p0 = samples.get(Math.max(0, i - 1));
            Segment p1 = samples.get(i);
            Segment p2 = samples.get(i + 1);
            Segment p3 = samples.get(Math.min(count - 1, i + 2));
            for (int step = 0; step <= subdivisions; step++) {
                float t = (float) step / (subdivisions + 1);
                out.add(new Segment(
                        catmullRom(p0.near(), p1.near(), p2.near(), p3.near(), t),
                        catmullRom(p0.far(), p1.far(), p2.far(), p3.far(), t)));
            }
        }
        out.add(samples.get(count - 1));
        return out;
    }

    private static Vector3f catmullRom(Vector3f p0, Vector3f p1, Vector3f p2, Vector3f p3, float t) {
        float t2 = t * t;
        float t3 = t2 * t;
        return new Vector3f(
                component(p0.x, p1.x, p2.x, p3.x, t, t2, t3),
                component(p0.y, p1.y, p2.y, p3.y, t, t2, t3),
                component(p0.z, p1.z, p2.z, p3.z, t, t2, t3));
    }

    private static float component(float a, float b, float c, float d, float t, float t2, float t3) {
        return 0.5F * ((2.0F * b)
                + (-a + c) * t
                + (2.0F * a - 5.0F * b + 4.0F * c - d) * t2
                + (-a + 3.0F * b - 3.0F * c + d) * t3);
    }

    /**
     * Pulls the near edge of an older sample toward the far one, so the ribbon narrows into its
     * tail instead of ending in a blunt rectangle.
     */
    private static Vector3f taperedNear(Segment segment, int index, int count) {
        float age = count <= 1 ? 1.0F : (float) index / (count - 1);
        return new Vector3f(segment.far()).lerp(segment.near(), 0.25F + 0.75F * age);
    }

    /** Oldest sample fully transparent, newest at the given opacity. */
    private static int alphaAt(int index, int count, float peak) {
        float fraction = count <= 1 ? 1.0F : (float) index / (count - 1);
        return MathHelper.clamp(Math.round(fraction * fraction * peak * 255.0F), 0, 255);
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
}
