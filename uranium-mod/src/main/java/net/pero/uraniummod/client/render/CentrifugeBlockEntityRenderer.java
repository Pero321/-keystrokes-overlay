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
	private static final Identifier BASE =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_base.png");
	private static final Identifier FOOT =
			Identifier.of(UraniumMod.MOD_ID, "textures/block/centrifuge_foot.png");

	private static final float PX = 1.0f / 16.0f;
	private static final int SIDES = 32;
	private static final int FULL_BRIGHT = LightmapTextureManager.MAX_LIGHT_COORDINATE;

	// v-bands of the 128x24 tower map, matching tools/gen_textures.py
	private static final float V_LOWER0 = 0.0f / 24.0f, V_LOWER1 = 4.0f / 24.0f;
	private static final float V_BODY0 = 4.0f / 24.0f, V_BODY1 = 20.0f / 24.0f;
	private static final float V_UPPER0 = 20.0f / 24.0f, V_UPPER1 = 24.0f / 24.0f;

	// The machine claims 3x3x2, so the model runs from -16 to +32 pixels in x and
	// z and 0 to 32 in y, centred on the controller block's middle.
	private static final float CX = 8.0f, CZ = 8.0f;
	private static final float FOOT_MIN = -16.0f, FOOT_MAX = 32.0f;
	private static final float COLLAR_R = 21.0f, BODY_R = 19.0f, GLOW_R = 19.4f;
	private static final float HOUSING_R = 13.0f, SHAFT_R = 3.0f;
	private static final float Y_PLINTH = 6.0f;      // top of the platform deck
	private static final float Y_FOOT = 7.5f;        // corner anchor blocks
	private static final float Y_BODY0 = 10.0f, Y_BODY1 = 23.0f;
	private static final float Y_UPPER = 27.0f, Y_HOUSING = 30.0f, Y_SHAFT = 32.0f;

	/** The skirt texture's design lives in rows 5..11; see tools/gen_textures.py. */
	private static final float SKIRT_V0 = 5.0f / 16.0f, SKIRT_V1 = 11.0f / 16.0f;

	public CentrifugeBlockEntityRenderer(BlockEntityRendererFactory.Context ctx) {
	}

	@Override
	public void render(CentrifugeBlockEntity be, float tickDelta, MatrixStack matrices,
	                   VertexConsumerProvider vertexConsumers, int light, int overlay) {
		boolean lit = be.getCachedState().contains(CentrifugeBlock.LIT)
				&& be.getCachedState().get(CentrifugeBlock.LIT);
		float spin = be.getSpin(tickDelta);
		float heat = be.getHeatFraction();

		matrices.push();
		matrices.translate(CX * PX, 0.0f, CZ * PX);

		// One layer at a time, and each buffer is fetched immediately before it is
		// used. VertexConsumerProvider.Immediate keeps a single active layer:
		// asking it for a different one calls draw() on the current buffer, which
		// ends it. Holding several buffers at once and interleaving writes throws
		// "Not building!" on the first write to a buffer that was already flushed.

		{   // Platform. Drawn as one box per block rather than a single 48px-wide
			// one: stretching a 16px texture over the whole span is the same
			// smearing that spoiled the earlier drum. The sides sample the
			// skirt band, the top gets tread plate.
			VertexConsumer skirt = vertexConsumers.getBuffer(
					RenderLayer.getEntityCutoutNoCull(BASE));
			for (int dx = -1; dx <= 1; dx++) {
				for (int dz = -1; dz <= 1; dz++) {
					float x0 = (dx * 16.0f - CX) * PX;
					float z0 = (dz * 16.0f - CZ) * PX;
					boxSides(matrices, skirt, x0, 0.0f, z0,
							x0 + 16.0f * PX, Y_PLINTH * PX, z0 + 16.0f * PX,
							SKIRT_V0, SKIRT_V1, light, overlay);
				}
			}
		}

		{   // tread-plate deck on top of the platform
			VertexConsumer deck = vertexConsumers.getBuffer(
					RenderLayer.getEntityCutoutNoCull(DECK));
			for (int dx = -1; dx <= 1; dx++) {
				for (int dz = -1; dz <= 1; dz++) {
					float x0 = (dx * 16.0f - CX) * PX;
					float z0 = (dz * 16.0f - CZ) * PX;
					boxTop(matrices, deck, x0, Y_PLINTH * PX, z0,
							x0 + 16.0f * PX, z0 + 16.0f * PX, light, overlay);
				}
			}
		}

		{   // anchor blocks at the four corners, so the base is not a bare slab
			VertexConsumer foot = vertexConsumers.getBuffer(
					RenderLayer.getEntityCutoutNoCull(FOOT));
			for (int sx = -1; sx <= 1; sx += 2) {
				for (int sz = -1; sz <= 1; sz += 2) {
					float cx = sx * 19.0f - CX;
					float cz = sz * 19.0f - CZ;
					box(matrices, foot, (cx - 5.0f) * PX, 0.0f, (cz - 5.0f) * PX,
							(cx + 5.0f) * PX, Y_FOOT * PX, (cz + 5.0f) * PX,
							light, overlay, 0xFFFFFFFF);
				}
			}
		}

		{   // steel: collars, housing, and the turning drum
			VertexConsumer tower = vertexConsumers.getBuffer(
					RenderLayer.getEntityCutoutNoCull(TOWER));
			cylinder(matrices, tower, COLLAR_R * PX, Y_PLINTH * PX, Y_BODY0 * PX,
					V_LOWER0, V_LOWER1, light, overlay, 0xFFFFFFFF);
			cylinder(matrices, tower, COLLAR_R * PX, Y_BODY1 * PX, Y_UPPER * PX,
					V_UPPER0, V_UPPER1, light, overlay, 0xFFFFFFFF);
			cylinder(matrices, tower, HOUSING_R * PX, Y_UPPER * PX, Y_HOUSING * PX,
					V_UPPER0, V_UPPER1, light, overlay, 0xFFFFFFFF);

			matrices.push();
			matrices.multiply(RotationAxis.POSITIVE_Y.rotation(spin));
			cylinder(matrices, tower, BODY_R * PX, Y_BODY0 * PX, Y_BODY1 * PX,
					V_BODY0, V_BODY1, light, overlay, 0xFFFFFFFF);
			matrices.pop();
		}

		{   // deck over the collar, or you can see straight down inside the tower
			VertexConsumer deck = vertexConsumers.getBuffer(
					RenderLayer.getEntityCutoutNoCull(DECK));
			disc(matrices, deck, COLLAR_R * PX, Y_UPPER * PX, light, overlay, 0xFFFFFFFF);
		}

		{   // rotor port on top of the housing
			VertexConsumer rotorTop = vertexConsumers.getBuffer(
					RenderLayer.getEntityCutoutNoCull(ROTOR_TOP));
			disc(matrices, rotorTop, HOUSING_R * PX, Y_HOUSING * PX, light, overlay, 0xFFFFFFFF);
		}

		{   // the drive shaft runs faster than the drum it is geared to
			VertexConsumer shaftBuf = vertexConsumers.getBuffer(
					RenderLayer.getEntityCutoutNoCull(SHAFT));
			matrices.push();
			matrices.multiply(RotationAxis.POSITIVE_Y.rotation(spin * 2.5f));
			cylinder(matrices, shaftBuf, SHAFT_R * PX, Y_HOUSING * PX, Y_SHAFT * PX,
					0.0f, 1.0f, light, overlay, 0xFFFFFFFF);
			for (int i = 0; i < 3; i++) {
				matrices.push();
				matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(i * 120.0f));
				matrices.translate(8.0f * PX, 0.0f, 0.0f);
				cylinder(matrices, shaftBuf, 2.0f * PX, Y_HOUSING * PX,
						(Y_HOUSING + 2.4f) * PX, 0.0f, 1.0f, light, overlay, 0xFFFFFFFF);
				matrices.pop();
			}
			matrices.pop();
		}

		// Emissive passes last, since they are translucent. Drawn at full lightmap
		// so the windows glow in the dark instead of merely being green.
		if (heat > 0.02f || lit) {
			float pulse = 0.78f + 0.22f * MathHelper.sin(spin * 0.7f);
			int alpha = (int) (MathHelper.clamp(heat, 0.0f, 1.0f) * pulse * 255.0f);
			if (alpha > 4) {
				int tint = (alpha << 24) | 0x00FFFFFF;

				{
					VertexConsumer glow = vertexConsumers.getBuffer(
							RenderLayer.getEntityTranslucentEmissive(TOWER_GLOW));
					matrices.push();
					matrices.multiply(RotationAxis.POSITIVE_Y.rotation(spin));
					cylinder(matrices, glow, GLOW_R * PX, Y_BODY0 * PX, Y_BODY1 * PX,
							V_BODY0, V_BODY1, FULL_BRIGHT, overlay, tint);
					matrices.pop();
				}

				{
					VertexConsumer portGlow = vertexConsumers.getBuffer(
							RenderLayer.getEntityTranslucentEmissive(ROTOR_TOP_GLOW));
					disc(matrices, portGlow, HOUSING_R * PX, (Y_HOUSING + 0.05f) * PX,
							FULL_BRIGHT, overlay, tint);
				}
			}
		}

		matrices.pop();
	}

	/** The four upright faces of a box, sampling a horizontal band of the texture. */
	private static void boxSides(MatrixStack matrices, VertexConsumer vc,
	                             float x0, float y0, float z0, float x1, float y1, float z1,
	                             float v0, float v1, int light, int overlay) {
		MatrixStack.Entry e = matrices.peek();
		float[][] faces = {
				{x1, y1, z0, x0, y1, z0, x0, y0, z0, x1, y0, z0, 0, 0, -1},
				{x0, y1, z1, x1, y1, z1, x1, y0, z1, x0, y0, z1, 0, 0, 1},
				{x1, y1, z1, x1, y1, z0, x1, y0, z0, x1, y0, z1, 1, 0, 0},
				{x0, y1, z0, x0, y1, z1, x0, y0, z1, x0, y0, z0, -1, 0, 0},
		};
		float[][] uv = {{0, v0}, {1, v0}, {1, v1}, {0, v1}};
		for (float[] f : faces) {
			for (int i = 0; i < 4; i++) {
				put(vc, e, f[i * 3], f[i * 3 + 1], f[i * 3 + 2], uv[i][0], uv[i][1],
						light, overlay, f[12], f[13], f[14], 0xFFFFFFFF);
			}
		}
	}

	/** Just the top face of a box. */
	private static void boxTop(MatrixStack matrices, VertexConsumer vc,
	                           float x0, float y, float z0, float x1, float z1,
	                           int light, int overlay) {
		MatrixStack.Entry e = matrices.peek();
		float[][] c = {{x0, y, z0}, {x1, y, z0}, {x1, y, z1}, {x0, y, z1}};
		float[][] uv = {{0, 0}, {1, 0}, {1, 1}, {0, 1}};
		for (int i = 0; i < 4; i++) {
			put(vc, e, c[i][0], c[i][1], c[i][2], uv[i][0], uv[i][1],
					light, overlay, 0.0f, 1.0f, 0.0f, 0xFFFFFFFF);
		}
	}

	/** Axis-aligned box, used for the corner feet. */
	private static void box(MatrixStack matrices, VertexConsumer vc,
	                        float x0, float y0, float z0, float x1, float y1, float z1,
	                        int light, int overlay, int tint) {
		MatrixStack.Entry e = matrices.peek();
		float[][] faces = {
				{x0, y1, z0, x1, y1, z0, x1, y1, z1, x0, y1, z1, 0, 1, 0},    // up
				{x0, y0, z1, x1, y0, z1, x1, y0, z0, x0, y0, z0, 0, -1, 0},   // down
				{x1, y1, z0, x0, y1, z0, x0, y0, z0, x1, y0, z0, 0, 0, -1},   // north
				{x0, y1, z1, x1, y1, z1, x1, y0, z1, x0, y0, z1, 0, 0, 1},    // south
				{x1, y1, z1, x1, y1, z0, x1, y0, z0, x1, y0, z1, 1, 0, 0},    // east
				{x0, y1, z0, x0, y1, z1, x0, y0, z1, x0, y0, z0, -1, 0, 0},   // west
		};
		float[][] uv = {{0, 0}, {1, 0}, {1, 1}, {0, 1}};
		for (float[] f : faces) {
			for (int i = 0; i < 4; i++) {
				put(vc, e, f[i * 3], f[i * 3 + 1], f[i * 3 + 2], uv[i][0], uv[i][1],
						light, overlay, f[12], f[13], f[14], tint);
			}
		}
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

	// the machine is drawn from the controller but spans 3x3x2, so it must not
	// be culled when the controller block itself leaves view
	@Override
	public boolean rendersOutsideBoundingBox(CentrifugeBlockEntity be) {
		return true;
	}
}
