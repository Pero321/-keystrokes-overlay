package net.pero.uraniummod.client.render;

import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.block.entity.BlockEntityRenderer;
import net.minecraft.client.render.block.entity.BlockEntityRendererFactory;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;
import net.pero.uraniummod.UraniumMod;
import net.pero.uraniummod.block.CentrifugeBlock;
import net.pero.uraniummod.block.entity.CentrifugeBlockEntity;

/**
 * Draws the centrifuge's moving parts.
 *
 * <p>The plinth and feed pipe stay in the baked JSON model — they never move, so
 * there is no reason to pay for them every frame. Everything here is generated as
 * triangles rather than boxes, which is what lets the drums be actual cylinders:
 * the JSON model format cannot express one.
 */
public class CentrifugeBlockEntityRenderer implements BlockEntityRenderer<CentrifugeBlockEntity> {
	private static final Identifier DRUM =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_drum.png");
	private static final Identifier DRUM_ON =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_drum_on_still.png");
	private static final Identifier CAP =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_cap.png");
	private static final Identifier DRUM_TOP =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_drum_top.png");
	private static final Identifier DRUM_TOP_ON =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_drum_top_on_still.png");
	private static final Identifier ARM =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_arm.png");

	private static final float PX = 1.0f / 16.0f;
	private static final int SIDES = 12;

	/** Drum centres in block space, matching the plinth cut-outs in the model. */
	private static final float[][] DRUMS = {
			{4.0f, 4.0f}, {12.0f, 4.0f}, {8.0f, 11.0f},
	};
	private static final float DRUM_R = 3.0f;
	private static final float DRUM_Y0 = 3.0f;
	private static final float DRUM_Y1 = 12.0f;
	private static final float CAP_R = 3.5f;
	private static final float CAP_Y1 = 14.0f;

	public CentrifugeBlockEntityRenderer(BlockEntityRendererFactory.Context ctx) {
	}

	@Override
	public void render(CentrifugeBlockEntity be, float tickDelta, MatrixStack matrices,
	                   VertexConsumerProvider vertexConsumers, int light, int overlay) {
		boolean lit = be.getCachedState().contains(CentrifugeBlock.LIT)
				&& be.getCachedState().get(CentrifugeBlock.LIT);
		float spin = be.getSpin(tickDelta);
		float arm = be.getArmPhase(tickDelta);

		// vertex colour can only darken, so pulse between dimmed and full white.
		// This replaces the old animated texture, which cannot work here: only
		// atlas sprites animate, and these textures are bound directly.
		int tint = 0xFFFFFFFF;
		if (be.getWorld() != null && lit) {
			float t = (be.getWorld().getTime() + tickDelta) * 0.18f;
			int v = 0xCC + (int) ((MathHelper.sin(t) * 0.5f + 0.5f) * 0x33);
			tint = 0xFF000000 | (v << 16) | (v << 8) | v;
		}

		VertexConsumer drum = vertexConsumers.getBuffer(
				RenderLayer.getEntityCutoutNoCull(lit ? DRUM_ON : DRUM));
		VertexConsumer cap = vertexConsumers.getBuffer(RenderLayer.getEntityCutoutNoCull(CAP));
		VertexConsumer top = vertexConsumers.getBuffer(
				RenderLayer.getEntityCutoutNoCull(lit ? DRUM_TOP_ON : DRUM_TOP));
		VertexConsumer armBuf = vertexConsumers.getBuffer(RenderLayer.getEntityCutoutNoCull(ARM));

		for (int i = 0; i < DRUMS.length; i++) {
			float cx = DRUMS[i][0] * PX;
			float cz = DRUMS[i][1] * PX;

			// the spinning body. Alternate drums turn the other way, the way a
			// real cascade is counter-balanced.
			matrices.push();
			matrices.translate(cx, 0.0f, cz);
			matrices.multiply(RotationAxis.POSITIVE_Y.rotation(i % 2 == 0 ? spin : -spin));
			cylinder(matrices, drum, DRUM_R * PX, DRUM_Y0 * PX, DRUM_Y1 * PX, light, overlay);
			matrices.pop();

			// the collar and its port stay put while the body turns inside them
			matrices.push();
			matrices.translate(cx, 0.0f, cz);
			cylinder(matrices, cap, CAP_R * PX, DRUM_Y1 * PX, CAP_Y1 * PX, light, overlay);
			disc(matrices, top, CAP_R * PX, CAP_Y1 * PX, light, overlay, tint);
			matrices.pop();

			// gold arm, rocking in time with the drums. Aim it away from the
			// centre of the block so it leans out over open air instead of
			// across its own drum.
			float yaw = (float) Math.toDegrees(Math.atan2(cx - 0.5f, cz - 0.5f));
			float lean = 38.0f + MathHelper.sin(arm + i * 2.1f) * 12.0f;
			matrices.push();
			matrices.translate(cx, CAP_Y1 * PX, cz);
			matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(yaw));
			matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(lean));
			cylinder(matrices, armBuf, 0.9f * PX, 0.0f, 5.0f * PX, light, overlay);
			matrices.pop();
		}
	}

	/** Emits an open-ended prism approximating a cylinder about the local Y axis. */
	private static void cylinder(MatrixStack matrices, VertexConsumer vc,
	                             float radius, float y0, float y1, int light, int overlay) {
		MatrixStack.Entry entry = matrices.peek();
		for (int i = 0; i < SIDES; i++) {
			float a0 = (float) (Math.PI * 2.0 * i / SIDES);
			float a1 = (float) (Math.PI * 2.0 * (i + 1) / SIDES);
			float x0 = MathHelper.cos(a0) * radius, z0 = MathHelper.sin(a0) * radius;
			float x1 = MathHelper.cos(a1) * radius, z1 = MathHelper.sin(a1) * radius;
			// wrap the texture once around the circumference, so the markings on
			// the casing visibly travel as the drum turns
			float u0 = i / (float) SIDES;
			float u1 = (i + 1) / (float) SIDES;
			float nx = MathHelper.cos((a0 + a1) * 0.5f);
			float nz = MathHelper.sin((a0 + a1) * 0.5f);

			put(vc, entry, x0, y1, z0, u0, 0.0f, light, overlay, nx, 0.0f, nz);
			put(vc, entry, x1, y1, z1, u1, 0.0f, light, overlay, nx, 0.0f, nz);
			put(vc, entry, x1, y0, z1, u1, 1.0f, light, overlay, nx, 0.0f, nz);
			put(vc, entry, x0, y0, z0, u0, 1.0f, light, overlay, nx, 0.0f, nz);
		}
	}

	/** Caps a cylinder with a fan of quads, so the port texture reads as a disc. */
	private static void disc(MatrixStack matrices, VertexConsumer vc,
	                         float radius, float y, int light, int overlay, int tint) {
		MatrixStack.Entry entry = matrices.peek();
		for (int i = 0; i < SIDES; i++) {
			float a0 = (float) (Math.PI * 2.0 * i / SIDES);
			float a1 = (float) (Math.PI * 2.0 * (i + 1) / SIDES);
			float x0 = MathHelper.cos(a0) * radius, z0 = MathHelper.sin(a0) * radius;
			float x1 = MathHelper.cos(a1) * radius, z1 = MathHelper.sin(a1) * radius;
			float u0 = 0.5f + MathHelper.cos(a0) * 0.5f, v0 = 0.5f + MathHelper.sin(a0) * 0.5f;
			float u1 = 0.5f + MathHelper.cos(a1) * 0.5f, v1 = 0.5f + MathHelper.sin(a1) * 0.5f;

			put(vc, entry, 0.0f, y, 0.0f, 0.5f, 0.5f, light, overlay, 0.0f, 1.0f, 0.0f, tint);
			put(vc, entry, x0, y, z0, u0, v0, light, overlay, 0.0f, 1.0f, 0.0f, tint);
			put(vc, entry, x1, y, z1, u1, v1, light, overlay, 0.0f, 1.0f, 0.0f, tint);
			put(vc, entry, 0.0f, y, 0.0f, 0.5f, 0.5f, light, overlay, 0.0f, 1.0f, 0.0f, tint);
		}
	}

	private static void put(VertexConsumer vc, MatrixStack.Entry entry,
	                        float x, float y, float z, float u, float v,
	                        int light, int overlay, float nx, float ny, float nz) {
		put(vc, entry, x, y, z, u, v, light, overlay, nx, ny, nz, 0xFFFFFFFF);
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
