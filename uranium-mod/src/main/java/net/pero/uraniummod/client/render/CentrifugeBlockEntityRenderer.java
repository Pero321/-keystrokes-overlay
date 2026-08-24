package net.pero.uraniummod.client.render;

import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.block.entity.BlockEntityRenderer;
import net.minecraft.client.render.block.entity.BlockEntityRendererFactory;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;
import net.pero.uraniummod.UraniumMod;
import net.pero.uraniummod.block.CentrifugeBlock;
import net.pero.uraniummod.block.entity.CentrifugeBlockEntity;

/**
 * Draws the centrifuge's rotor tower.
 *
 * <p>Only the plinth stays in the baked JSON model. Everything here is emitted
 * as triangles, which is what lets the tower be a real cylinder — the JSON model
 * format only expresses axis-aligned boxes, and has no animation at all.
 *
 * <p>The tower texture is 64x16 rather than 16x16 because the drum is roughly 39
 * block-pixels around but only 8 tall; a square texture would have to stretch
 * about 2.4x to wrap it. It also carries no left-right shading, because entity
 * render layers light curved surfaces from the vertex normals, and baked-in
 * shading would rotate with the drum.
 */
public class CentrifugeBlockEntityRenderer implements BlockEntityRenderer<CentrifugeBlockEntity> {
	private static final Identifier TOWER =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_tower.png");
	private static final Identifier TOWER_GLOW =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_tower_glow.png");
	private static final Identifier ROTOR_TOP =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_rotor_top.png");
	private static final Identifier ROTOR_TOP_GLOW =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_rotor_top_glow.png");
	private static final Identifier SHAFT =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_shaft.png");
	private static final Identifier DECK =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_deck.png");

	private static final float PX = 1.0f / 16.0f;
	private static final int SIDES = 20;
	private static final int FULL_BRIGHT = LightmapTextureManager.MAX_LIGHT_COORDINATE;

	// v-bands of the tower map, matching tools/gen_textures.py
	private static final float V_LOWER0 = 0.0f / 16.0f, V_LOWER1 = 3.0f / 16.0f;
	private static final float V_BODY0 = 3.0f / 16.0f, V_BODY1 = 13.0f / 16.0f;
	private static final float V_UPPER0 = 13.0f / 16.0f, V_UPPER1 = 16.0f / 16.0f;

	private static final float COLLAR_R = 6.8f, BODY_R = 6.2f, GLOW_R = 6.32f;
	private static final float HOUSING_R = 4.2f, SHAFT_R = 1.0f;
	private static final float Y_BASE = 1.5f, Y_BODY0 = 3.5f, Y_BODY1 = 11.5f;
	private static final float Y_UPPER = 13.5f, Y_HOUSING = 15.0f, Y_SHAFT = 16.0f;

	public CentrifugeBlockEntityRenderer(BlockEntityRendererFactory.Context ctx) {
	}

	@Override
	public void render(CentrifugeBlockEntity be, float tickDelta, MatrixStack matrices,
	                   VertexConsumerProvider vertexConsumers, int light, int overlay) {
		boolean lit = be.getCachedState().contains(CentrifugeBlock.LIT)
				&& be.getCachedState().get(CentrifugeBlock.LIT);
		float spin = be.getSpin(tickDelta);
		float heat = be.getHeatFraction();

		VertexConsumer tower = vertexConsumers.getBuffer(RenderLayer.getEntityCutoutNoCull(TOWER));
		VertexConsumer rotorTop = vertexConsumers.getBuffer(
				RenderLayer.getEntityCutoutNoCull(ROTOR_TOP));
		VertexConsumer shaftBuf = vertexConsumers.getBuffer(
				RenderLayer.getEntityCutoutNoCull(SHAFT));
		VertexConsumer deck = vertexConsumers.getBuffer(
				RenderLayer.getEntityCutoutNoCull(DECK));

		matrices.push();
		matrices.translate(0.5f, 0.0f, 0.5f);

		// static armour: the collars and housing do not turn
		cylinder(matrices, tower, COLLAR_R * PX, Y_BASE * PX, Y_BODY0 * PX,
				V_LOWER0, V_LOWER1, light, overlay, 0xFFFFFFFF);
		cylinder(matrices, tower, COLLAR_R * PX, Y_BODY1 * PX, Y_UPPER * PX,
				V_UPPER0, V_UPPER1, light, overlay, 0xFFFFFFFF);
		// deck over the collar, or you can see straight down inside the tower
		disc(matrices, deck, COLLAR_R * PX, Y_UPPER * PX, light, overlay, 0xFFFFFFFF);
		cylinder(matrices, tower, HOUSING_R * PX, Y_UPPER * PX, Y_HOUSING * PX,
				V_UPPER0, V_UPPER1, light, overlay, 0xFFFFFFFF);
		disc(matrices, rotorTop, HOUSING_R * PX, Y_HOUSING * PX, light, overlay, 0xFFFFFFFF);

		// the rotor drum itself
		matrices.push();
		matrices.multiply(RotationAxis.POSITIVE_Y.rotation(spin));
		cylinder(matrices, tower, BODY_R * PX, Y_BODY0 * PX, Y_BODY1 * PX,
				V_BODY0, V_BODY1, light, overlay, 0xFFFFFFFF);
		matrices.pop();

		// the drive shaft runs faster than the drum it is geared to
		matrices.push();
		matrices.multiply(RotationAxis.POSITIVE_Y.rotation(spin * 2.5f));
		cylinder(matrices, shaftBuf, SHAFT_R * PX, Y_HOUSING * PX, Y_SHAFT * PX,
				0.0f, 1.0f, light, overlay, 0xFFFFFFFF);
		for (int i = 0; i < 3; i++) {
			matrices.push();
			matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(i * 120.0f));
			matrices.translate(2.6f * PX, 0.0f, 0.0f);
			cylinder(matrices, shaftBuf, 0.7f * PX, Y_HOUSING * PX, (Y_HOUSING + 0.9f) * PX,
					0.0f, 1.0f, light, overlay, 0xFFFFFFFF);
			matrices.pop();
		}
		matrices.pop();

		// Emissive pass. Drawn at full lightmap so the windows glow in the dark
		// instead of merely being green, which is what made the old model look
		// dead. Brightness follows heat, with a slow pulse on top.
		if (heat > 0.02f || lit) {
			float pulse = 0.78f + 0.22f * MathHelper.sin(spin * 0.7f);
			int alpha = (int) (MathHelper.clamp(heat, 0.0f, 1.0f) * pulse * 255.0f);
			if (alpha > 4) {
				int tint = (alpha << 24) | 0x00FFFFFF;
				VertexConsumer glow = vertexConsumers.getBuffer(
						RenderLayer.getEntityTranslucentEmissive(TOWER_GLOW));
				matrices.push();
				matrices.multiply(RotationAxis.POSITIVE_Y.rotation(spin));
				cylinder(matrices, glow, GLOW_R * PX, Y_BODY0 * PX, Y_BODY1 * PX,
						V_BODY0, V_BODY1, FULL_BRIGHT, overlay, tint);
				matrices.pop();

				VertexConsumer portGlow = vertexConsumers.getBuffer(
						RenderLayer.getEntityTranslucentEmissive(ROTOR_TOP_GLOW));
				disc(matrices, portGlow, HOUSING_R * PX, (Y_HOUSING + 0.02f) * PX,
						FULL_BRIGHT, overlay, tint);
			}
		}

		matrices.pop();
	}

	/** Open-ended prism approximating a cylinder about the local Y axis. */
	private static void cylinder(MatrixStack matrices, VertexConsumer vc, float radius,
	                             float y0, float y1, float v0, float v1,
	                             int light, int overlay, int tint) {
		MatrixStack.Entry entry = matrices.peek();
		for (int i = 0; i < SIDES; i++) {
			float a0 = (float) (Math.PI * 2.0 * i / SIDES);
			float a1 = (float) (Math.PI * 2.0 * (i + 1) / SIDES);
			float x0 = MathHelper.cos(a0) * radius, z0 = MathHelper.sin(a0) * radius;
			float x1 = MathHelper.cos(a1) * radius, z1 = MathHelper.sin(a1) * radius;
			float u0 = i / (float) SIDES, u1 = (i + 1) / (float) SIDES;
			float nx = MathHelper.cos((a0 + a1) * 0.5f);
			float nz = MathHelper.sin((a0 + a1) * 0.5f);

			put(vc, entry, x0, y1, z0, u0, v0, light, overlay, nx, 0.0f, nz, tint);
			put(vc, entry, x1, y1, z1, u1, v0, light, overlay, nx, 0.0f, nz, tint);
			put(vc, entry, x1, y0, z1, u1, v1, light, overlay, nx, 0.0f, nz, tint);
			put(vc, entry, x0, y0, z0, u0, v1, light, overlay, nx, 0.0f, nz, tint);
		}
	}

	/** Fan of quads capping a cylinder, so a radial texture reads as a disc. */
	private static void disc(MatrixStack matrices, VertexConsumer vc, float radius,
	                         float y, int light, int overlay, int tint) {
		MatrixStack.Entry entry = matrices.peek();
		for (int i = 0; i < SIDES; i++) {
			float a0 = (float) (Math.PI * 2.0 * i / SIDES);
			float a1 = (float) (Math.PI * 2.0 * (i + 1) / SIDES);
			float x0 = MathHelper.cos(a0) * radius, z0 = MathHelper.sin(a0) * radius;
			float x1 = MathHelper.cos(a1) * radius, z1 = MathHelper.sin(a1) * radius;
			float u0 = 0.5f + MathHelper.cos(a0) * 0.5f, w0 = 0.5f + MathHelper.sin(a0) * 0.5f;
			float u1 = 0.5f + MathHelper.cos(a1) * 0.5f, w1 = 0.5f + MathHelper.sin(a1) * 0.5f;

			put(vc, entry, 0.0f, y, 0.0f, 0.5f, 0.5f, light, overlay, 0.0f, 1.0f, 0.0f, tint);
			put(vc, entry, x0, y, z0, u0, w0, light, overlay, 0.0f, 1.0f, 0.0f, tint);
			put(vc, entry, x1, y, z1, u1, w1, light, overlay, 0.0f, 1.0f, 0.0f, tint);
			put(vc, entry, 0.0f, y, 0.0f, 0.5f, 0.5f, light, overlay, 0.0f, 1.0f, 0.0f, tint);
		}
	}

	private static void put(VertexConsumer vc, MatrixStack.Entry entry,
	                        float x, float y, float z, float u, float v,
	                        int light, int overlay, float nx, float ny, float nz, int tint) {
		vc.vertex(entry, x, y, z)
				.color(tint)
				.texture(u, v)
				.overlay(overlay)
				.light(light)
				.normal(entry, nx, ny, nz);
	}

	@Override
	public boolean rendersOutsideBoundingBox(CentrifugeBlockEntity be) {
		return false;
	}
}
