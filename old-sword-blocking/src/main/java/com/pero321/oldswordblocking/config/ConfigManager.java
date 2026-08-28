package com.pero321.oldswordblocking.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.pero321.oldswordblocking.OldSwordBlocking;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;

public final class ConfigManager {

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Path PATH = FabricLoader.getInstance().getConfigDir().resolve("old-sword-blocking.json");

    private static ModConfig config = new ModConfig();

    private ConfigManager() {
    }

    public static ModConfig get() {
        return config;
    }

    public static void load() {
        if (!Files.exists(PATH)) {
            save();
            return;
        }
        try (Reader reader = Files.newBufferedReader(PATH)) {
            ModConfig loaded = GSON.fromJson(reader, ModConfig.class);
            if (loaded != null) {
                loaded.sanitise();
                config = loaded;
            }
        } catch (Exception e) {
            OldSwordBlocking.LOGGER.warn("Could not read {}, falling back to defaults", PATH, e);
            config = new ModConfig();
        }
    }

    public static void save() {
        try {
            Files.createDirectories(PATH.getParent());
            try (Writer writer = Files.newBufferedWriter(PATH)) {
                GSON.toJson(config, writer);
            }
        } catch (IOException e) {
            OldSwordBlocking.LOGGER.warn("Could not write {}", PATH, e);
        }
    }
}
