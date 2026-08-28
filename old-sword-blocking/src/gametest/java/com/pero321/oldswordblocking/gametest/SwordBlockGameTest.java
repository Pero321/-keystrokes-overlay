package com.pero321.oldswordblocking.gametest;

import com.pero321.oldswordblocking.client.BlockingState;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.gui.screen.world.WorldCreator;
import net.minecraft.client.option.Perspective;

/**
 * Drives a real client: builds a creative world, puts a diamond sword in the hand, holds the use
 * key and checks that the mod actually enters and leaves the block state. Screenshots of each stage
 * land in {@code run/screenshots/}, so the pose can be eyeballed as well as asserted.
 *
 * <p>Run with {@code ./gradlew runGametestClient}.
 */
public class SwordBlockGameTest implements FabricClientGameTest {

    @Override
    public void runTest(ClientGameTestContext context) {
        try (TestSingleplayerContext singleplayer = context.worldBuilder()
                .adjustSettings(creator -> {
                    creator.setGameMode(WorldCreator.Mode.CREATIVE);
                    creator.setCheatsEnabled(true);
                })
                .create()) {

            singleplayer.getClientWorld().waitForChunksRender();

            context.runOnClient(client -> client.player.networkHandler.sendChatCommand("give @s diamond_sword"));
            context.waitTicks(20);
            context.runOnClient(client -> client.player.getInventory().setSelectedSlot(0));
            // Long enough for the "Gave 1 Diamond Sword" chat line to fade, so the shots stay clean.
            context.waitTicks(220);

            assertState(context, false, "before the use key was ever held");
            context.takeScreenshot("01-sword-idle");

            context.getInput().holdKey(options -> options.useKey);
            context.waitTicks(10);
            assertState(context, true, "while the use key was held with a sword");
            context.takeScreenshot("02-sword-blocking");

            // The other half of the illusion: your own body in F5.
            context.runOnClient(client -> client.options.setPerspective(Perspective.THIRD_PERSON_BACK));
            context.waitTicks(10);
            context.takeScreenshot("03-sword-blocking-third-person");
            context.runOnClient(client -> client.options.setPerspective(Perspective.FIRST_PERSON));
            context.waitTicks(5);

            context.getInput().releaseKey(options -> options.useKey);
            context.waitTicks(10);
            assertState(context, false, "after the use key was released");
            context.takeScreenshot("04-sword-released");

            // An empty hand must never pose, however hard you hold right click.
            context.runOnClient(client -> client.player.getInventory().setSelectedSlot(1));
            context.getInput().holdKey(options -> options.useKey);
            context.waitTicks(10);
            assertState(context, false, "while the use key was held with an empty hand");
            context.getInput().releaseKey(options -> options.useKey);
        }
    }

    private static void assertState(ClientGameTestContext context, boolean expected, String situation) {
        boolean actual = context.computeOnClient(client -> BlockingState.isActive());
        if (actual != expected) {
            String diagnosis = context.computeOnClient(client -> "screen=" + client.currentScreen
                    + " focused=" + client.isWindowFocused()
                    + " useKey=" + client.options.useKey.isPressed()
                    + " usingItem=" + (client.player != null && client.player.isUsingItem())
                    + " gameMode=" + client.interactionManager.getCurrentGameMode()
                    + " mainHand=" + (client.player == null ? "?" : client.player.getMainHandStack())
                    + " isBlockingItem=" + (client.player != null && BlockingState.isBlockingItem(client.player.getMainHandStack())));
            throw new AssertionError("Expected blocking=" + expected + " but was " + actual + " " + situation
                    + " [" + diagnosis + "]");
        }
    }
}
