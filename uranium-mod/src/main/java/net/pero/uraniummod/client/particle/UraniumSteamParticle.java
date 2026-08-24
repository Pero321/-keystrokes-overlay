package net.pero.uraniummod.client.particle;

import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleFactory;
import net.minecraft.client.particle.ParticleTextureSheet;
import net.minecraft.client.particle.SpriteBillboardParticle;
import net.minecraft.client.particle.SpriteProvider;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.SimpleParticleType;

/**
 * Vapour off the centrifuge: drifts up, swells, and fades from a hot green to a
 * washed-out grey as it cools, so a plume reads as thinning out with height
 * rather than just vanishing.
 */
public class UraniumSteamParticle extends SpriteBillboardParticle {
	private final SpriteProvider spriteProvider;

	protected UraniumSteamParticle(ClientWorld world, double x, double y, double z,
	                               double vx, double vy, double vz,
	                               SpriteProvider spriteProvider) {
		super(world, x, y, z, 0.0, 0.0, 0.0);
		this.spriteProvider = spriteProvider;
		this.velocityX = vx + (random.nextDouble() - 0.5) * 0.01;
		this.velocityY = vy + 0.01 + random.nextDouble() * 0.015;
		this.velocityZ = vz + (random.nextDouble() - 0.5) * 0.01;
		this.gravityStrength = -0.008f;                 // buoyant, so it rises
		this.maxAge = 34 + random.nextInt(22);
		this.scale = 0.10f + random.nextFloat() * 0.06f;
		this.velocityMultiplier = 0.92f;
		setColor(0.62f, 0.94f, 0.68f);
		setSpriteForAge(spriteProvider);
	}

	@Override
	public void tick() {
		super.tick();
		setSpriteForAge(spriteProvider);
		float life = age / (float) maxAge;
		this.scale += 0.0032f;                          // swells as it cools
		this.alpha = (1.0f - life) * 0.85f;
		// bleed the green out towards plain steam
		this.red = 0.62f + 0.30f * life;
		this.green = 0.94f;
		this.blue = 0.68f + 0.26f * life;
	}

	@Override
	public ParticleTextureSheet getType() {
		return ParticleTextureSheet.PARTICLE_SHEET_TRANSLUCENT;
	}

	public static class Factory implements ParticleFactory<SimpleParticleType> {
		private final SpriteProvider spriteProvider;

		public Factory(SpriteProvider spriteProvider) {
			this.spriteProvider = spriteProvider;
		}

		@Override
		public Particle createParticle(SimpleParticleType type, ClientWorld world,
		                               double x, double y, double z,
		                               double vx, double vy, double vz) {
			return new UraniumSteamParticle(world, x, y, z, vx, vy, vz, spriteProvider);
		}
	}
}
