package net.pero.uraniummod.effect;

import net.minecraft.entity.effect.StatusEffect;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;

public final class ModEffects {

	public static final RegistryKey<StatusEffect> RADIATION_KEY = RegistryKey.of(
			RegistryKeys.STATUS_EFFECT, Identifier.of(UraniumMod.MOD_ID, "radiation"));

	public static RegistryEntry<StatusEffect> RADIATION;

	private ModEffects() {
	}

	public static void register() {
		RADIATION = Registry.registerReference(
				Registries.STATUS_EFFECT, RADIATION_KEY, new RadiationStatusEffect());
	}
}
