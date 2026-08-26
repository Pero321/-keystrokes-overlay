package net.pero.uraniummod.effect;

import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.damage.DamageType;
import net.minecraft.entity.effect.StatusEffect;
import net.minecraft.entity.effect.StatusEffectCategory;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;

/**
 * Damage over time from handling unrefined uranium.
 *
 * <p>It ignores armour points on purpose -- a breastplate does not stop
 * radiation. The only defence is the shielded suit, which works by preventing
 * the effect from being applied at all rather than by soaking the damage.
 */
public class RadiationStatusEffect extends StatusEffect {

	/** Ticks between damage instances at level I; halved per level above that. */
	private static final int BASE_INTERVAL = 60;

	public static final RegistryKey<DamageType> RADIATION_DAMAGE = RegistryKey.of(
			RegistryKeys.DAMAGE_TYPE, Identifier.of(UraniumMod.MOD_ID, "radiation"));

	public RadiationStatusEffect() {
		super(StatusEffectCategory.HARMFUL, 0x6BE04A);
	}

	@Override
	public boolean canApplyUpdateEffect(int duration, int amplifier) {
		int interval = Math.max(10, BASE_INTERVAL >> amplifier);
		return duration % interval == 0;
	}

	@Override
	public boolean applyUpdateEffect(ServerWorld world, LivingEntity entity, int amplifier) {
		DamageSource source = world.getDamageSources().create(RADIATION_DAMAGE);
		entity.damage(world, source, 1.0f + amplifier);
		return true;
	}
}
