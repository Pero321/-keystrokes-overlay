package com.pero321.oldswordblocking.gametest;

import com.pero321.oldswordblocking.client.BlockingState;
import com.pero321.oldswordblocking.trail.SwordTrail;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.gui.screen.world.WorldCreator;
import net.minecraft.client.option.Perspective;

/**
 * Drives a real client through every visual the mod adds: the block stance in both perspectives,
 * the swing trail, and the HUD with a deliberately battered set of armour so the warning marks
 * show. Screenshots of each stage land in {@code run/screenshots/}, so the poses and the layout can
 * be eyeballed as well as asserted.
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

            // Quiet commands keep the screenshots clean.
            run(context, "gamerule sendCommandFeedback false");
            run(context, "item replace entity @s weapon.mainhand with minecraft:diamond_sword[minecraft:damage=1400]");
            run(context, "item replace entity @s armor.head with minecraft:diamond_helmet[minecraft:damage=350]");
            run(context, "item replace entity @s armor.chest with minecraft:diamond_chestplate[minecraft:damage=200]");
            run(context, "item replace entity @s armor.legs with minecraft:iron_leggings[minecraft:damage=100]");
            run(context, "item replace entity @s armor.feet with minecraft:golden_boots[minecraft:damage=40]");
            context.runOnClient(client -> client.player.getInventory().setSelectedSlot(0));

            // Long enough for the command and warning chat lines to fade away.
            context.waitTicks(220);

            assertState(context, false, "before the use key was ever held");
            context.takeScreenshot("01-hud-and-idle-pose");

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

            // Swinging: the blade should be dragging a streak behind it.
            // A swing lasts six ticks, so look at it while it is still going and the streak has
            // had a couple of frames to build up.
            context.getInput().holdKey(options -> options.attackKey);
            context.waitTicks(2);
            boolean trailing = context.computeOnClient(client -> !SwordTrail.isEmpty());
            if (!trailing) {
                throw new AssertionError("Swinging a sword left no trail samples behind");
            }
            context.takeScreenshot("04-sword-trail");
            context.waitTicks(1);
            context.takeScreenshot("05-sword-trail-later");
            context.getInput().releaseKey(options -> options.attackKey);
            context.waitTicks(20);

            // An empty hand must never pose, however hard you hold right click.
            context.runOnClient(client -> client.player.getInventory().setSelectedSlot(1));
            context.getInput().holdKey(options -> options.useKey);
            context.waitTicks(10);
            assertState(context, false, "while the use key was held with an empty hand");
            context.getInput().releaseKey(options -> options.useKey);
        }
    }

    private static void run(ClientGameTestContext context, String command) {
        context.runOnClient(client -> client.player.networkHandler.sendChatCommand(command));
        context.waitTicks(2);
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
