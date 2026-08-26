package net.pero.uraniummod.recipe;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.item.ItemStack;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.recipe.Ingredient;
import net.minecraft.recipe.RecipeSerializer;
import net.minecraft.recipe.RecipeType;
import net.minecraft.recipe.SingleStackRecipe;
import net.minecraft.recipe.book.RecipeBookCategory;
import net.minecraft.util.math.random.Random;

import java.util.Optional;

/**
 * One centrifuge operation: an ingredient in, a guaranteed product out, and an
 * optional second product that only appears some of the time.
 *
 * <p>The chanced byproduct is the whole point of the machine. Enrichment does
 * not convert an input into a single output the way smelting does -- almost
 * everything that comes out is the common isotope, and the rare one is what you
 * leave the machine running for.
 *
 * <p>Process time and the heat the machine must reach are per-recipe, so a
 * datapack can make a harder recipe take longer or demand a hotter machine
 * without touching the block.
 */
public class CentrifugingRecipe extends SingleStackRecipe {

	private final Optional<ItemStack> byproduct;
	private final float byproductChance;
	private final int processingTime;
	private final int heat;

	public CentrifugingRecipe(String group, Ingredient ingredient, ItemStack result,
	                          Optional<ItemStack> byproduct, float byproductChance,
	                          int processingTime, int heat) {
		super(group, ingredient, result);
		this.byproduct = byproduct;
		this.byproductChance = byproductChance;
		this.processingTime = processingTime;
		this.heat = heat;
	}

	/** The product every run yields. */
	public ItemStack getResult() {
		return result();
	}

	/**
	 * Rolls the byproduct for one run. Empty when the recipe has none, or when
	 * this run simply did not hit.
	 */
	public ItemStack rollByproduct(Random random) {
		if (byproduct.isEmpty() || random.nextFloat() >= byproductChance) {
			return ItemStack.EMPTY;
		}
		return byproduct.get().copy();
	}

	/** The byproduct itself, ignoring chance -- for output-slot compatibility checks. */
	public ItemStack getByproduct() {
		return byproduct.orElse(ItemStack.EMPTY);
	}

	public float getByproductChance() {
		return byproductChance;
	}

	public int getProcessingTime() {
		return processingTime;
	}

	/** Heat the machine has to reach before this recipe will run at all. */
	public int getHeat() {
		return heat;
	}

	@Override
	public RecipeSerializer<? extends SingleStackRecipe> getSerializer() {
		return ModRecipes.CENTRIFUGING_SERIALIZER;
	}

	@Override
	public RecipeType<? extends SingleStackRecipe> getType() {
		return ModRecipes.CENTRIFUGING;
	}

	@Override
	public RecipeBookCategory getRecipeBookCategory() {
		return ModRecipes.CENTRIFUGING_CATEGORY;
	}

	public static class Serializer implements RecipeSerializer<CentrifugingRecipe> {

		public static final MapCodec<CentrifugingRecipe> CODEC = RecordCodecBuilder.mapCodec(instance ->
				instance.group(
						com.mojang.serialization.Codec.STRING.optionalFieldOf("group", "")
								.forGetter(CentrifugingRecipe::getGroup),
						Ingredient.CODEC.fieldOf("ingredient")
								.forGetter(CentrifugingRecipe::ingredient),
						ItemStack.VALIDATED_CODEC.fieldOf("result")
								.forGetter(CentrifugingRecipe::getResult),
						ItemStack.VALIDATED_CODEC.optionalFieldOf("byproduct")
								.forGetter(r -> r.byproduct),
						com.mojang.serialization.Codec.FLOAT.optionalFieldOf("byproduct_chance", 0.0f)
								.forGetter(CentrifugingRecipe::getByproductChance),
						com.mojang.serialization.Codec.INT.optionalFieldOf("processing_time", 160)
								.forGetter(CentrifugingRecipe::getProcessingTime),
						com.mojang.serialization.Codec.INT.optionalFieldOf("heat", 600)
								.forGetter(CentrifugingRecipe::getHeat)
				).apply(instance, CentrifugingRecipe::new));

		public static final PacketCodec<RegistryByteBuf, CentrifugingRecipe> PACKET_CODEC =
				PacketCodec.tuple(
						PacketCodecs.STRING, CentrifugingRecipe::getGroup,
						Ingredient.PACKET_CODEC, CentrifugingRecipe::ingredient,
						ItemStack.PACKET_CODEC, CentrifugingRecipe::getResult,
						ItemStack.OPTIONAL_PACKET_CODEC.collect(PacketCodecs::optional),
								r -> r.byproduct,
						PacketCodecs.FLOAT, CentrifugingRecipe::getByproductChance,
						PacketCodecs.VAR_INT, CentrifugingRecipe::getProcessingTime,
						PacketCodecs.VAR_INT, CentrifugingRecipe::getHeat,
						CentrifugingRecipe::new);

		@Override
		public MapCodec<CentrifugingRecipe> codec() {
			return CODEC;
		}

		/**
		 * Still abstract on the interface, but deprecated: since 1.21.2 recipes
		 * are not sent to clients wholesale, only their displays. Nothing on the
		 * client side of this mod needs the recipe -- the screen reads process
		 * time and heat off the synced property delegate -- so this exists to
		 * satisfy the contract.
		 */
		@Deprecated
		@Override
		public PacketCodec<RegistryByteBuf, CentrifugingRecipe> packetCodec() {
			return PACKET_CODEC;
		}
	}
}
