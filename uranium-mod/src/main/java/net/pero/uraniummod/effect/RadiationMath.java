package net.pero.uraniummod.effect;

/**
 * The exposure arithmetic, kept free of any Minecraft type so it can be run and
 * checked on its own. The rest of the radiation system is thin plumbing around
 * these three numbers; this is the part with decisions in it.
 */
public final class RadiationMath {

	/** Slots of armour that can be shielded. A full set is total protection. */
	public static final int ARMOR_PIECES = 4;

	/** A raw uranium block is nine raw uranium wrapped in nothing. */
	public static final int BLOCK_WORTH = 9;

	/** Raw units at or above which exposure steps up a level. */
	public static final int LEVEL_2_THRESHOLD = 16;
	public static final int LEVEL_3_THRESHOLD = 64;

	private RadiationMath() {
	}

	/**
	 * Each worn piece stops a quarter of the exposure; the full suit stops all
	 * of it. Rounding is deliberate: three pieces against a single raw uranium
	 * rounds to zero, so a nearly-complete suit is not punished for the last
	 * unit of a rounding error.
	 */
	public static int applyShielding(int exposure, int piecesWorn) {
		if (piecesWorn >= ARMOR_PIECES) {
			return 0;
		}
		if (piecesWorn <= 0) {
			return exposure;
		}
		return Math.round(exposure * (1.0f - 0.25f * piecesWorn));
	}

	/** Level I for a handful, II for a stack, III for a serious pile. */
	public static int amplifierFor(int exposure) {
		if (exposure >= LEVEL_3_THRESHOLD) {
			return 2;
		}
		if (exposure >= LEVEL_2_THRESHOLD) {
			return 1;
		}
		return 0;
	}
}
