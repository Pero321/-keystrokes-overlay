package net.pero.uraniummod.particle;

import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.particle.SimpleParticleType;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;

public class ModParticles {
	/** Green-tinged vapour vented by a running centrifuge. */
	public static final SimpleParticleType URANIUM_STEAM = Registry.register(
			Registries.PARTICLE_TYPE,
			Identifier.of(UraniumMod.MOD_ID, "uranium_steam"),
			FabricParticleTypes.simple());

	public static void registerParticles() {
		UraniumMod.LOGGER.info("Registering particles for " + UraniumMod.MOD_ID);
	}
}
