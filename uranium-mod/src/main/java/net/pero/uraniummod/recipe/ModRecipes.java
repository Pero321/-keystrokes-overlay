package net.pero.uraniummod.recipe;

import net.minecraft.recipe.RecipeSerializer;
import net.minecraft.recipe.RecipeType;
import net.minecraft.recipe.book.RecipeBookCategory;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;
import net.pero.uraniummod.UraniumMod;

public final class ModRecipes {

	public static final RecipeType<CentrifugingRecipe> CENTRIFUGING = new RecipeType<>() {
		@Override
		public String toString() {
			return UraniumMod.MOD_ID + ":centrifuging";
		}
	};

	public static final CentrifugingRecipe.Serializer CENTRIFUGING_SERIALIZER =
			new CentrifugingRecipe.Serializer();

	public static final RecipeBookCategory CENTRIFUGING_CATEGORY = new RecipeBookCategory();

	private ModRecipes() {
	}

	public static void register() {
		Identifier id = Identifier.of(UraniumMod.MOD_ID, "centrifuging");
		Registry.register(Registries.RECIPE_TYPE, id, CENTRIFUGING);
		Registry.register(Registries.RECIPE_SERIALIZER, id, CENTRIFUGING_SERIALIZER);
		Registry.register(Registries.RECIPE_BOOK_CATEGORY, id, CENTRIFUGING_CATEGORY);
	}
}
