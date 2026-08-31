package com.pero321.oldswordblocking.client;

import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.pero321.oldswordblocking.OldSwordBlocking;
import com.pero321.oldswordblocking.config.ConfigManager;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import com.pero321.oldswordblocking.hud.GearHud;
import com.pero321.oldswordblocking.hud.InfoHud;
import com.pero321.oldswordblocking.projectile.LandingMarkers;
import com.pero321.oldswordblocking.projectile.ProjectileTrails;
import com.pero321.oldswordblocking.trail.SwordTrail;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderEvents;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import org.lwjgl.glfw.GLFW;

import static net.fabricmc.fabric.api.client.command.v2.ClientCommandManager.literal;

public class OldSwordBlockingClient implements ClientModInitializer {

    private static KeyBinding toggleKey;
    private static final GearHud GEAR_HUD = new GearHud();

    @Override
    public void onInitializeClient() {
        ConfigManager.load();

        // Unbound by default so it can never fight with an existing key.
        toggleKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.oldswordblocking.toggle",
                GLFW.GLFW_KEY_UNKNOWN,
                KeyBinding.Category.GAMEPLAY));

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (toggleKey.wasPressed()) {
                boolean now = !ConfigManager.get().enabled;
                ConfigManager.get().enabled = now;
                ConfigManager.save();
                if (!now) {
                    BlockingState.reset();
                }
                if (client.player != null) {
                    client.player.sendMessage(Text.translatable(
                            now ? "text.oldswordblocking.enabled" : "text.oldswordblocking.disabled"), true);
                }
            }
            BlockingState.tick(client);
            GEAR_HUD.tick(client);
            LandingMarkers.tick(client);
            if (client.player == null) {
                SwordTrail.clear();
                ProjectileTrails.clear();
            }
        });

        WorldRenderEvents.AFTER_ENTITIES.register(context -> {
            ProjectileTrails.render(context);
            LandingMarkers.render(context);
        });

        HudElementRegistry.addLast(Identifier.of(OldSwordBlocking.MOD_ID, "info"), new InfoHud());
        HudElementRegistry.addLast(Identifier.of(OldSwordBlocking.MOD_ID, "gear"), GEAR_HUD);

        ClientCommandRegistrationCallback.EVENT.register((dispatcher, access) -> dispatcher.register(buildCommand()));

        OldSwordBlocking.LOGGER.info("Old Sword Blocking ready (client side only, no packets are sent)");
    }

    private static LiteralArgumentBuilder<FabricClientCommandSource> buildCommand() {
        return literal("oldswordblock")
                .executes(context -> status(context.getSource()))
                .then(literal("status").executes(context -> status(context.getSource())))
                .then(literal("toggle").executes(context -> {
                    boolean now = !ConfigManager.get().enabled;
                    ConfigManager.get().enabled = now;
                    ConfigManager.save();
                    if (!now) {
                        BlockingState.reset();
                    }
                    return status(context.getSource());
                }))
                .then(literal("reload").executes(context -> {
                    ConfigManager.load();
                    BlockingState.reset();
                    context.getSource().sendFeedback(Text.translatable("text.oldswordblocking.reloaded"));
                    return 1;
                }));
    }

    private static int status(FabricClientCommandSource source) {
        source.sendFeedback(Text.translatable(ConfigManager.get().enabled
                ? "text.oldswordblocking.enabled"
                : "text.oldswordblocking.disabled"));
        return 1;
    }
}
