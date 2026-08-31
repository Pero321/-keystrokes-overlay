package com.pero321.oldswordblocking.projectile;

import com.pero321.oldswordblocking.config.ConfigManager;
import com.pero321.oldswordblocking.config.ModConfig;
import com.pero321.oldswordblocking.mixin.PersistentProjectileEntityAccessor;
import com.pero321.oldswordblocking.trail.Ribbon;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.Entity;
import net.minecraft.entity.projectile.ArrowEntity;
import net.minecraft.entity.projectile.PersistentProjectileEntity;
import net.minecraft.entity.projectile.SpectralArrowEntity;
import net.minecraft.entity.projectile.TridentEntity;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.Vec3d;
import org.joml.Vector3f;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * The streak behind a trident or an arrow in flight.
 *
 * <p>Same idea as the sword's: a short history of where the thing has been, stitched into a
 * fading ribbon. The difference is that a projectile is a point rather than a blade, so each frame's
 * two edges are made by stepping sideways from the flight path, square to the line from the camera.
 * The ribbon therefore always faces you, whatever angle the shot crosses at.
 */
public final class ProjectileTrails {

    private static final Identifier TEXTURE = Identifier.of("oldswordblocking", "textures/trail.png");
    private static final RenderLayer LAYER = RenderLayers.entityTranslucentEmissiveNoOutline(TEXTURE);

    private static final int ARROW_COLOR = 0xE6E2D6;
    private static final int SPECTRAL_COLOR = 0xF2C94C;
    private static final int TRIDENT_COLOR = 0x4FD8CF;

    /** Flight path per entity, newest last, in world coordinates. */
    private static final Map<Integer, Deque<Vec3d>> PATHS = new HashMap<>();

    private ProjectileTrails() {
    }

    public static void clear() {
        PATHS.clear();
    }

    public static void render(WorldRenderContext context) {
        MinecraftClient client = MinecraftClient.getInstance();
        ModConfig.ProjectileConfig config = ConfigManager.get().projectiles;
        if (!ConfigManager.get().enabled || !config.trail || client.world == null) {
            clear();
            return;
        }

        float tickProgress = client.getRenderTickCounter().getTickProgress(false);
        Vec3d camera = client.gameRenderer.getCamera().getCameraPos();
        Set<Integer> alive = new HashSet<>();

        for (Entity entity : client.world.getEntities()) {
            if (!(entity instanceof PersistentProjectileEntity projectile) || !isTrailed(projectile, config)) {
                continue;
            }
            // A landed projectile stops feeding the ribbon, and its tail drains away behind it.
            if (!((PersistentProjectileEntityAccessor) projectile).oldswordblocking$isInGround()) {
                alive.add(entity.getId());
                Deque<Vec3d> path = PATHS.computeIfAbsent(entity.getId(), id -> new ArrayDeque<>());
                path.addLast(entity.getLerpedPos(tickProgress));
                while (path.size() > Math.max(2, config.samples)) {
                    path.removeFirst();
                }
            }
        }

        // Anything that landed, was picked up or left the area drains one frame at a time.
        PATHS.entrySet().removeIf(entry -> {
            if (alive.contains(entry.getKey())) {
                return false;
            }
            entry.getValue().pollFirst();
            return entry.getValue().size() < 2;
        });

        if (PATHS.isEmpty()) {
            return;
        }

        float peak = MathHelper.clamp(config.opacity, 0.0F, 1.0F);
        MatrixStack matrices = context.matrices();
        var consumer = context.consumers().getBuffer(LAYER);

        for (Map.Entry<Integer, Deque<Vec3d>> entry : PATHS.entrySet()) {
            List<Ribbon.Segment> ribbon = billboard(entry.getValue(), camera, config.width);
            if (ribbon.size() < 2) {
                continue;
            }
            int rgb = colorFor(client, entry.getKey(), config);
            Ribbon.emit(consumer, matrices.peek(), ribbon,
                    (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF, peak, config.smoothing);
        }
    }

    /**
     * Turns a flight path into a strip that faces the camera: at each point, step half the width
     * either side, square to both the direction of travel and the line to the eye.
     */
    private static List<Ribbon.Segment> billboard(Deque<Vec3d> path, Vec3d camera, float halfWidth) {
        List<Vec3d> points = new ArrayList<>(path);
        List<Ribbon.Segment> ribbon = new ArrayList<>(points.size());

        for (int i = 0; i < points.size(); i++) {
            Vec3d point = points.get(i);
            Vec3d ahead = i + 1 < points.size() ? points.get(i + 1) : point;
            Vec3d behind = i > 0 ? points.get(i - 1) : point;
            Vec3d direction = ahead.subtract(behind);
            if (direction.lengthSquared() < 1.0E-6) {
                continue;
            }
            Vec3d toCamera = camera.subtract(point);
            Vec3d side = direction.crossProduct(toCamera);
            if (side.lengthSquared() < 1.0E-9) {
                continue;
            }
            side = side.normalize().multiply(halfWidth);

            // Relative to the camera, which is where the world render stack is rooted.
            Vec3d local = point.subtract(camera);
            ribbon.add(new Ribbon.Segment(
                    new Vector3f((float) (local.x - side.x), (float) (local.y - side.y), (float) (local.z - side.z)),
                    new Vector3f((float) (local.x + side.x), (float) (local.y + side.y), (float) (local.z + side.z))));
        }
        return ribbon;
    }

    private static boolean isTrailed(PersistentProjectileEntity projectile, ModConfig.ProjectileConfig config) {
        if (projectile instanceof TridentEntity) {
            return config.trailTridents;
        }
        return config.trailArrows;
    }

    private static int colorFor(MinecraftClient client, int entityId, ModConfig.ProjectileConfig config) {
        Entity entity = client.world == null ? null : client.world.getEntityById(entityId);
        if (entity instanceof TridentEntity) {
            return TRIDENT_COLOR;
        }
        if (entity instanceof SpectralArrowEntity) {
            return SPECTRAL_COLOR;
        }
        if (config.usePotionColor && entity instanceof ArrowEntity arrow) {
            int color = arrow.getColor();
            if (color != -1) {
                return color & 0xFFFFFF;
            }
        }
        return ARROW_COLOR;
    }
}
