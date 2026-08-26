package net.pero.uraniummod.effect;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Hand;
import net.pero.uraniummod.block.ModBlocks;
import net.pero.uraniummod.item.ModItems;

/**
 * Applies {@link RadiationStatusEffect} to players carrying unrefined uranium.
 *
 * <p>Only <em>raw</em> uranium is hot. Once it has been through the centrifuge
 * the isotopes are separated and stable enough to handle, so ingots, U-238,
 * U-235 and the refined block are all inert -- carrying them is safe.
 */
public final class RadiationHandler {

	/** How often exposure is recalculated. */
	private static final int CHECK_INTERVAL = 20;
	/** Longer than the check interval, so the effect never flickers off between checks. */
	private static final int EFFECT_DURATION = 100;

	private static final EquipmentSlot[] ARMOR_SLOTS = {
			EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET
	};

	private RadiationHandler() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTicks() % CHECK_INTERVAL != 0) {
				return;
			}
			for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
				tickPlayer(player);
			}
		});
	}

	private static void tickPlayer(ServerPlayerEntity player) {
		if (player.isCreative() || player.isSpectator()) {
			return;
		}

		int exposure = heldRawUnits(player);
		if (exposure <= 0) {
			return;
		}

		exposure = RadiationMath.applyShielding(exposure, countShieldedPieces(player));
		if (exposure <= 0) {
			return;
		}

		player.addStatusEffect(new StatusEffectInstance(
				ModEffects.RADIATION, EFFECT_DURATION,
				RadiationMath.amplifierFor(exposure), false, true, true));
	}

	/** Raw uranium the player is holding, in "one raw uranium" units. */
	private static int heldRawUnits(ServerPlayerEntity player) {
		int units = 0;
		for (Hand hand : Hand.values()) {
			units += rawUnits(player.getStackInHand(hand));
		}
		return units;
	}

	private static int rawUnits(ItemStack stack) {
		if (stack.isOf(ModItems.RAW_URANIUM)) {
			return stack.getCount();
		}
		if (stack.isOf(ModBlocks.RAW_URANIUM_BLOCK.asItem())) {
			return stack.getCount() * RadiationMath.BLOCK_WORTH;
		}
		return 0;
	}

	private static int countShieldedPieces(ServerPlayerEntity player) {
		int worn = 0;
		for (EquipmentSlot slot : ARMOR_SLOTS) {
			if (isShielded(player.getEquippedStack(slot))) {
				worn++;
			}
		}
		return worn;
	}

	private static boolean isShielded(ItemStack stack) {
		return stack.isOf(ModItems.SHIELDED_HELMET)
				|| stack.isOf(ModItems.SHIELDED_CHESTPLATE)
				|| stack.isOf(ModItems.SHIELDED_LEGGINGS)
				|| stack.isOf(ModItems.SHIELDED_BOOTS);
	}

}
