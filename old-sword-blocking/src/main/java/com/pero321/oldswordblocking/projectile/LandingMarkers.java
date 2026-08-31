package com.pero321.oldswordblocking.projectile;

import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
import com.pero321.oldswordblocking.mixin.PersistentProjectileEntityAccessor;
import com.pero321.oldswordblocking.trail.Ribbon;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.Camera;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.Entity;
import net.minecraft.entity.projectile.PersistentProjectileEntity;
import net.minecraft.entity.projectile.TridentEntity;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.Vec3d;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Marks where a trident or an arrow came down, so it can be found again.
 *
 * <p>A mark is dropped the moment a projectile sticks, and taken away again once you have walked
 * over to it, once the thing itself is gone from that spot — picked up, or broken — or after its
 * lifetime runs out. Marks are drawn through walls, which is the whole point of a waypoint.
 */
public final class LandingMarkers {

    private static final int TRIDENT_COLOR = 0xFF4FD8CF;
    private static final int ARROW_COLOR = 0xFFFFCC44;
    private static final Identifier TEXTURE = Identifier.of("oldswordblocking", "textures/trail.png");
    /**
     * The see-through text pipeline: translucent, no depth test, and it takes any texture. That
     * last part is what makes it usable for plain geometry, and the no depth test is the whole
     * point of a waypoint — a mark you can only see when nothing is in the way is not a waypoint.
     */
    private static final RenderLayer MARK_LAYER = RenderLayers.textSeeThrough(TEXTURE);

    /** Segments around the ring. Thirty two is smooth at any distance you would look from. */
    private static final int RING_SEGMENTS = 32;

    /** Beyond this the projectile is not loaded on the client, so "it is gone" cannot be judged. */
    private static final double TRACKING_RANGE = 32.0;
    /** How close a landed projectile has to be to count as the one this mark is for. */
    private static final double SAME_SPOT = 2.25;

    private record Marker(Vec3d pos, long created, boolean trident) {
    }

    private static final List<Marker> MARKERS = new ArrayList<>();
    /** Projectiles already considered, so one landing makes one mark. */
    private static final Set<Integer> HANDLED = new HashSet<>();

    private LandingMarkers() {
    }

    public static void clear() {
        MARKERS.clear();
        HANDLED.clear();
    }

    public static void tick(MinecraftClient client) {
        ModConfig.ProjectileConfig config = ConfigManager.get().projectiles;
        if (!ConfigManager.get().enabled || !config.markers
                || client.world == null || client.player == null) {
            clear();
            return;
        }

        long now = client.world.getTime();
        List<Vec3d> landed = new ArrayList<>();

        for (Entity entity : client.world.getEntities()) {
            if (!(entity instanceof PersistentProjectileEntity projectile)
                    || !((PersistentProjectileEntityAccessor) projectile).oldswordblocking$isInGround()) {
                continue;
            }
            landed.add(entity.getEntityPos());
            if (!HANDLED.add(entity.getId()) || !shouldMark(projectile, client, config)) {
                continue;
            }
            MARKERS.add(new Marker(entity.getEntityPos(), now, projectile instanceof TridentEntity));
        }

        while (MARKERS.size() > config.maxMarkers) {
            MARKERS.removeFirst();
        }

        Vec3d player = client.player.getEntityPos();
        MARKERS.removeIf(marker -> {
            if (now - marker.created() > config.lifetimeSeconds * 20L) {
                return true;
            }
            double distance = player.distanceTo(marker.pos());
            if (distance < config.clearWithinBlocks) {
                return true;
            }
            // Only conclude "it is not there any more" where the client would actually see it.
            return distance < TRACKING_RANGE
                    && landed.stream().noneMatch(spot -> spot.squaredDistanceTo(marker.pos()) < SAME_SPOT);
        });

        HANDLED.removeIf(id -> client.world.getEntityById(id) == null);
    }

    public static void render(WorldRenderContext context) {
        ModConfig.ProjectileConfig config = ConfigManager.get().projectiles;
        MinecraftClient client = MinecraftClient.getInstance();
        if (MARKERS.isEmpty() || !ConfigManager.get().enabled || !config.markers) {
            return;
        }

        Camera camera = client.gameRenderer.getCamera();
        Vec3d eye = camera.getCameraPos();
        MatrixStack matrices = context.matrices();

        var consumer = context.consumers().getBuffer(MARK_LAYER);
        float time = (client.world == null ? 0 : client.world.getTime())
                + client.getRenderTickCounter().getTickProgress(false);
        // One slow breath, so a mark reads as alive without flickering.
        float pulse = 0.5F + 0.5F * MathHelper.sin(time * 0.12F);

        for (Marker marker : List.copyOf(MARKERS)) {
            int color = marker.trident() ? TRIDENT_COLOR : ARROW_COLOR;

            if (config.ring) {
                matrices.push();
                matrices.translate(marker.pos().x - eye.x, marker.pos().y - eye.y + 0.02,
                        marker.pos().z - eye.z);
                ring(consumer, matrices.peek(), config.ringRadius * (1.0F + 0.07F * pulse),
                        config.ringRadius * 0.22F, color, 0.55F + 0.45F * pulse);
                matrices.pop();
            }

            if (!config.mark) {
                continue;
            }

            matrices.push();
            matrices.translate(marker.pos().x - eye.x, marker.pos().y - eye.y + 0.6, marker.pos().z - eye.z);
            matrices.multiply(camera.getRotation());
            // Grow with distance so the mark keeps roughly the same size on screen. A fixed scale
            // is fine for a nameplate a few blocks away and invisible for a shot that went forty.
            double eyeDistance = eye.distanceTo(marker.pos());
            float scale = 0.025F * config.markerScale
                    * (float) MathHelper.clamp(eyeDistance / 6.0, 1.6, 18.0);
            // Vanilla's nameplate space: both axes flipped, so +Y runs down and text comes out
            // upright. The mark's own quads are given in that same space.
            matrices.scale(-scale, -scale, scale);

            // The mark is drawn as geometry rather than a font glyph: it stays crisp at any
            // distance, takes its colour directly, and needs no font metrics to centre.
            var entry = matrices.peek();
            quad(consumer, entry, -1.6F, -14.0F, 1.6F, -4.6F, color);
            quad(consumer, entry, -1.6F, -2.6F, 1.6F, 0.9F, color);

            matrices.pop();
        }
    }

    /** A flat ring lying on the ground, in the space already translated to the marked spot. */
    private static void ring(VertexConsumer consumer, MatrixStack.Entry entry, float radius,
                             float thickness, int argb, float alphaScale) {
        int alpha = MathHelper.clamp(Math.round(((argb >>> 24) & 0xFF) * alphaScale), 0, 255);
        int red = (argb >> 16) & 0xFF;
        int green = (argb >> 8) & 0xFF;
        int blue = argb & 0xFF;
        float inner = Math.max(0.0F, radius - thickness);

        for (int i = 0; i < RING_SEGMENTS; i++) {
            float a = (float) (i * 2.0 * Math.PI / RING_SEGMENTS);
            float b = (float) ((i + 1) * 2.0 * Math.PI / RING_SEGMENTS);
            float cosA = MathHelper.cos(a);
            float sinA = MathHelper.sin(a);
            float cosB = MathHelper.cos(b);
            float sinB = MathHelper.sin(b);

            // Both windings again: a horizontal ring is seen from above or below depending on
            // where you stand, and every layer used here culls back faces.
            flat(consumer, entry, inner * cosA, inner * sinA, red, green, blue, alpha);
            flat(consumer, entry, radius * cosA, radius * sinA, red, green, blue, alpha);
            flat(consumer, entry, radius * cosB, radius * sinB, red, green, blue, alpha);
            flat(consumer, entry, inner * cosB, inner * sinB, red, green, blue, alpha);

            flat(consumer, entry, inner * cosB, inner * sinB, red, green, blue, alpha);
            flat(consumer, entry, radius * cosB, radius * sinB, red, green, blue, alpha);
            flat(consumer, entry, radius * cosA, radius * sinA, red, green, blue, alpha);
            flat(consumer, entry, inner * cosA, inner * sinA, red, green, blue, alpha);
        }
    }

    private static void flat(VertexConsumer consumer, MatrixStack.Entry entry, float x, float z,
                             int red, int green, int blue, int alpha) {
        consumer.vertex(entry, x, 0.0F, z)
                .color(red, green, blue, alpha)
                .texture(0.9F, 0.5F)
                .light(Ribbon.FULL_BRIGHT);
    }

    /** An axis aligned rectangle in the billboard's own space, facing the camera. */
    private static void quad(VertexConsumer consumer, MatrixStack.Entry entry,
                             float x1, float y1, float x2, float y2, int argb) {
        int alpha = (argb >>> 24) & 0xFF;
        int red = (argb >> 16) & 0xFF;
        int green = (argb >> 8) & 0xFF;
        int blue = argb & 0xFF;
        // Both windings: which way round a billboard faces depends on the camera, and the
        // layer culls back faces.
        vertex(consumer, entry, x1, y1, red, green, blue, alpha);
        vertex(consumer, entry, x2, y1, red, green, blue, alpha);
        vertex(consumer, entry, x2, y2, red, green, blue, alpha);
        vertex(consumer, entry, x1, y2, red, green, blue, alpha);
        vertex(consumer, entry, x1, y2, red, green, blue, alpha);
        vertex(consumer, entry, x2, y2, red, green, blue, alpha);
        vertex(consumer, entry, x2, y1, red, green, blue, alpha);
        vertex(consumer, entry, x1, y1, red, green, blue, alpha);
    }

    private static void vertex(VertexConsumer consumer, MatrixStack.Entry entry, float x, float y,
                               int red, int green, int blue, int alpha) {
        consumer.vertex(entry, x, y, 0.0F)
                .color(red, green, blue, alpha)
                .texture(0.9F, 0.5F)
                .light(Ribbon.FULL_BRIGHT);
    }

    private static boolean shouldMark(PersistentProjectileEntity projectile, MinecraftClient client,
                                      ModConfig.ProjectileConfig config) {
        boolean trident = projectile instanceof TridentEntity;
        if (trident ? !config.markTridents : !config.markArrows) {
            return false;
        }
        return !config.onlyMine || projectile.getOwner() == client.player;
    }
}
