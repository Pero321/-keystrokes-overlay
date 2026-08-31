package com.pero321.oldswordblocking.gametest;

import com.pero321.oldswordblocking.client.BlockingState;
import com.pero321.oldswordblocking.trail.SwordTrail;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.gui.screen.world.WorldCreator;
import net.minecraft.client.option.Perspective;
import net.minecraft.world.gen.WorldPresets;

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
        // Software rendering and world generation are fighting over the same few cores here, and
        // the harness only allows ten seconds for the world to load.
        context.runOnClient(client -> {
            client.options.getViewDistance().setValue(3);
            client.options.getSimulationDistance().setValue(3);
        });

        try (TestSingleplayerContext singleplayer = context.worldBuilder()
                .adjustSettings(creator -> {
                    creator.setGameMode(WorldCreator.Mode.CREATIVE);
                    creator.setCheatsEnabled(true);
                    // Superflat: terrain generation is the slowest part of this test by far, and
                    // none of it is what we are looking at.
                    creator.getNormalWorldTypes().stream()
                            .filter(type -> type.preset() != null && type.preset().matchesKey(WorldPresets.FLAT))
                            .findFirst()
                            .ifPresent(creator::setWorldType);
                    System.out.println("[WORLDDEBUG] types=" + creator.getNormalWorldTypes().size()
                            + " chosen=" + creator.getWorldType().getName().getString());
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
            swingAndShoot(context, "04-diamond", true, 3);

            // Every material gets its own streak colour and its own swing, so compare the
            // heaviest blade against the lightest across the same frames of the animation.
            run(context, "item replace entity @s weapon.mainhand with minecraft:netherite_sword[minecraft:damage=1000]");
            context.waitTicks(10);
            swingAndShoot(context, "05-netherite", false, 3);

            run(context, "item replace entity @s weapon.mainhand with minecraft:golden_sword[minecraft:damage=8]");
            context.waitTicks(10);
            swingAndShoot(context, "06-golden", false, 3);

            // With a screen open the HUD must draw nothing at all: every item drawn in a frame
            // takes a slot in a size capped GPU atlas, and a full creative tab can fill it alone.
            context.getInput().pressKey(options -> options.inventoryKey);
            context.waitTicks(10);
            context.takeScreenshot("07-inventory-open");
            context.runOnClient(client -> client.setScreen(null));
            context.waitTicks(10);

            // An empty hand must never pose, however hard you hold right click.
            context.runOnClient(client -> client.player.getInventory().setSelectedSlot(1));
            context.getInput().holdKey(options -> options.useKey);
            context.waitTicks(10);
            assertState(context, false, "while the use key was held with an empty hand");
            context.getInput().releaseKey(options -> options.useKey);
        }
    }

    /** Swings once and captures the first few ticks, while the animation is still running. */
    private static void swingAndShoot(ClientGameTestContext context, String name, boolean assertTrail, int frames) {
        context.getInput().holdKey(options -> options.attackKey);
        for (int tick = 1; tick <= frames; tick++) {
            context.waitTicks(1);
            if (tick == 2 && assertTrail && context.computeOnClient(client -> SwordTrail.isEmpty())) {
                throw new AssertionError("Swinging a sword left no trail samples behind");
            }
            context.takeScreenshot(name + "-tick-" + tick);
        }
        context.getInput().releaseKey(options -> options.attackKey);
        context.waitTicks(20);
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
