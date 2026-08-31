import com.pero321.oldswordblocking.config.ModConfig;
import com.pero321.oldswordblocking.swing.SwingAnimations;
import com.pero321.oldswordblocking.swing.SwingProfile;
import net.minecraft.client.util.math.MatrixStack;
import org.joml.Vector3f;

/**
 * Runs the real swing transform outside the game and prints the blade tip's path for each
 * material, so the animation can be measured — reach, when it peaks, whether it returns to rest —
 * without needing a renderer.
 *
 * <pre>
 * cd old-sword-blocking &amp;&amp; ./gradlew build
 * MC=$(find .gradle/loom-cache/minecraftMaven -name "*-v2.jar" ! -name "*sources*" | head -1)
 * LIBS=$(find ~/.gradle/caches/modules-2 -name "*.jar" ! -name "*sources*" | tr '\n' ':')
 * javac -cp "build/classes/java/main:$MC:$LIBS" -d /tmp/probe tools/SwingProbe.java
 * java -cp "build/classes/java/main:$MC:$LIBS/tmp/probe" SwingProbe
 * </pre>
 */
public final class SwingProbe {

    /** Where the tip of a vanilla blade sits in hand space; the same point the streak uses. */
    private static final Vector3f BLADE_TIP = new Vector3f(0.07F, 0.80F, 0.28F);

    private static final String[] BLADES = {
            "golden_sword", "wooden_sword", "stone_sword", "iron_sword",
            "diamond_sword", "netherite_sword", "trident", "mace"
    };

    private SwingProbe() {
    }

    public static void main(String[] args) {
        ModConfig.SwingConfig config = new ModConfig.SwingConfig();

        print("vanilla", SwingProfile.VANILLA);
        for (String blade : BLADES) {
            print(blade, SwingAnimations.profileForPath(blade, config));
        }
    }

    private static void print(String name, SwingProfile profile) {
        StringBuilder line = new StringBuilder(name);
        for (int step = 0; step <= 50; step++) {
            MatrixStack matrices = new MatrixStack();
            // applyEquipOffset for a right handed player holding a fully equipped item.
            matrices.translate(0.56F, -0.52F, -0.72F);
            SwingAnimations.apply(matrices, step / 50.0F, 1, profile);
            Vector3f tip = matrices.peek().getPositionMatrix().transformPosition(new Vector3f(BLADE_TIP));
            line.append(String.format(" %.4f,%.4f,%.4f", tip.x, tip.y, tip.z));
        }
        System.out.println(line);
    }
}
