import net.pero.uraniummod.effect.RadiationMath;

public class RadiationMathTest {
    static int fails = 0;
    static void eq(String what, int got, int want) {
        if (got != want) { System.out.printf("FAIL %-46s got %d want %d%n", what, got, want); fails++; }
        else System.out.printf("ok   %-46s = %d%n", what, got);
    }

    public static void main(String[] args) {
        // shielding: each piece stops a quarter, the full set stops everything
        eq("bare hands, 32 raw",            RadiationMath.applyShielding(32, 0), 32);
        eq("1 piece, 32 raw",               RadiationMath.applyShielding(32, 1), 24);
        eq("2 pieces, 32 raw",              RadiationMath.applyShielding(32, 2), 16);
        eq("3 pieces, 32 raw",              RadiationMath.applyShielding(32, 3), 8);
        eq("full suit, 32 raw",             RadiationMath.applyShielding(32, 4), 0);
        eq("full suit, a whole stack",      RadiationMath.applyShielding(64, 4), 0);
        eq("more than a full suit",         RadiationMath.applyShielding(64, 9), 0);

        // the full suit must be total protection at ANY exposure, or a big
        // enough pile would leak through the one defence the mod offers
        for (int e = 0; e <= 1000; e++) {
            if (RadiationMath.applyShielding(e, 4) != 0) {
                System.out.println("FAIL full suit leaked at exposure " + e); fails++; break;
            }
        }
        System.out.println("ok   full suit blocks every exposure 0..1000");

        // shielding must never make exposure worse, and must never go negative
        for (int e = 0; e <= 600; e++)
            for (int p = 0; p <= 4; p++) {
                int r = RadiationMath.applyShielding(e, p);
                if (r < 0 || r > e) {
                    System.out.printf("FAIL exposure %d, %d pieces -> %d%n", e, p, r); fails++;
                }
            }
        System.out.println("ok   shielding is monotonic and never negative");

        // level thresholds
        eq("1 raw is level I",              RadiationMath.amplifierFor(1), 0);
        eq("15 raw is still level I",       RadiationMath.amplifierFor(15), 0);
        eq("16 raw steps to level II",      RadiationMath.amplifierFor(16), 1);
        eq("63 raw is still level II",      RadiationMath.amplifierFor(63), 1);
        eq("64 raw steps to level III",     RadiationMath.amplifierFor(64), 2);
        eq("a stack of blocks caps at III", RadiationMath.amplifierFor(64 * 9), 2);

        // amplifier must never exceed II -- a higher level would index past the
        // damage ramp the effect defines
        for (int e = 0; e <= 10000; e++) {
            int a = RadiationMath.amplifierFor(e);
            if (a < 0 || a > 2) { System.out.println("FAIL amplifier " + a + " at " + e); fails++; break; }
        }
        System.out.println("ok   amplifier stays within 0..2");

        // a full stack of raw uranium BLOCKS is the worst case a player can hold
        eq("64 raw blocks in raw units",
           64 * RadiationMath.BLOCK_WORTH, 576);
        eq("...which is level III",
           RadiationMath.amplifierFor(64 * RadiationMath.BLOCK_WORTH), 2);
        eq("...and a full suit still zeroes it",
           RadiationMath.applyShielding(576, 4), 0);

        System.out.println(fails == 0 ? "\nALL PASS" : "\n" + fails + " FAILURES");
        if (fails > 0) System.exit(1);
    }
}
