package net.pero.uraniummod.block.entity;

import net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerFactory;
import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.Inventories;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.registry.RegistryWrapper;
import net.minecraft.screen.PropertyDelegate;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.collection.DefaultedList;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.world.World;
import net.pero.uraniummod.block.CentrifugeBlock;
import net.pero.uraniummod.item.ModItems;
import net.pero.uraniummod.screen.CentrifugeScreenHandler;

/**
 * Refines raw uranium into ingots, but only once it is hot enough.
 *
 * <p>Heat climbs while the block is receiving a redstone signal and bleeds away
 * when it is not. Nothing is processed below {@link #OPERATING_HEAT}, so the
 * player has to power the machine and wait for it to come up to temperature.
 */
public class CentrifugeBlockEntity extends BlockEntity
		implements ExtendedScreenHandlerFactory<BlockPos>, ImplementedInventory {

	public static final int INPUT_SLOT = 0;
	public static final int OUTPUT_SLOT = 1;

	public static final int MAX_HEAT = 1000;
	/** Keep in sync with THRESHOLD in tools/gen_textures.py, which draws the gauge notch. */
	public static final int OPERATING_HEAT = 600;
	public static final int HEAT_PER_TICK = 2;
	public static final int COOL_PER_TICK = 3;
	public static final int PROCESS_TIME = 160;

	// property delegate indices, shared with the screen handler
	public static final int PROP_HEAT = 0;
	public static final int PROP_PROGRESS = 1;
	public static final int PROP_MAX_HEAT = 2;
	public static final int PROP_PROCESS_TIME = 3;
	public static final int PROP_OPERATING_HEAT = 4;
	public static final int PROP_COUNT = 5;

	private final DefaultedList<ItemStack> inventory = DefaultedList.ofSize(2, ItemStack.EMPTY);
	private int heat = 0;
	private int progress = 0;

	private final PropertyDelegate propertyDelegate = new PropertyDelegate() {
		@Override
		public int get(int index) {
			return switch (index) {
				case PROP_HEAT -> heat;
				case PROP_PROGRESS -> progress;
				case PROP_MAX_HEAT -> MAX_HEAT;
				case PROP_PROCESS_TIME -> PROCESS_TIME;
				case PROP_OPERATING_HEAT -> OPERATING_HEAT;
				default -> 0;
			};
		}

		@Override
		public void set(int index, int value) {
			switch (index) {
				case PROP_HEAT -> heat = value;
				case PROP_PROGRESS -> progress = value;
				default -> {
				}
			}
		}

		@Override
		public int size() {
			return PROP_COUNT;
		}
	};

	public CentrifugeBlockEntity(BlockPos pos, BlockState state) {
		super(ModBlockEntities.CENTRIFUGE, pos, state);
	}

	@Override
	public DefaultedList<ItemStack> getItems() {
		return inventory;
	}

	public int getHeat() {
		return heat;
	}

	// ------------------------------------------------------------------ ticking

	public static void tick(World world, BlockPos pos, BlockState state, CentrifugeBlockEntity be) {
		if (world.isClient()) {
			return;
		}

		boolean powered = world.isReceivingRedstonePower(pos);
		boolean dirty = false;

		if (powered) {
			if (be.heat < MAX_HEAT) {
				be.heat = Math.min(MAX_HEAT, be.heat + HEAT_PER_TICK);
				dirty = true;
			}
		} else if (be.heat > 0) {
			be.heat = Math.max(0, be.heat - COOL_PER_TICK);
			dirty = true;
		}

		if (be.isHotEnough() && be.canProcess()) {
			be.progress++;
			if (be.progress >= PROCESS_TIME) {
				be.process();
				be.progress = 0;
			}
			dirty = true;
		} else if (be.progress > 0) {
			// losing temperature undoes the run in progress rather than pausing it
			be.progress = Math.max(0, be.progress - 2);
			dirty = true;
		}

		boolean lit = be.isHotEnough();
		if (state.get(CentrifugeBlock.LIT) != lit) {
			world.setBlockState(pos, state.with(CentrifugeBlock.LIT, lit), Block.NOTIFY_ALL);
			dirty = true;
		}

		if (dirty) {
			markDirty(world, pos, state);
		}
	}

	public boolean isHotEnough() {
		return heat >= OPERATING_HEAT;
	}

	private boolean canProcess() {
		ItemStack input = inventory.get(INPUT_SLOT);
		if (!input.isOf(ModItems.RAW_URANIUM)) {
			return false;
		}
		ItemStack output = inventory.get(OUTPUT_SLOT);
		if (output.isEmpty()) {
			return true;
		}
		return output.isOf(ModItems.URANIUM_INGOT)
				&& output.getCount() < output.getMaxCount();
	}

	private void process() {
		inventory.get(INPUT_SLOT).decrement(1);
		ItemStack output = inventory.get(OUTPUT_SLOT);
		if (output.isEmpty()) {
			inventory.set(OUTPUT_SLOT, new ItemStack(ModItems.URANIUM_INGOT, 1));
		} else {
			output.increment(1);
		}
	}

	// ------------------------------------------------------------------ sidedness

	@Override
	public int[] getAvailableSlots(Direction side) {
		return side == Direction.DOWN ? new int[]{OUTPUT_SLOT} : new int[]{INPUT_SLOT};
	}

	@Override
	public boolean canInsert(int slot, ItemStack stack, Direction side) {
		return slot == INPUT_SLOT && stack.isOf(ModItems.RAW_URANIUM);
	}

	@Override
	public boolean canExtract(int slot, ItemStack stack, Direction side) {
		return slot == OUTPUT_SLOT;
	}

	@Override
	public boolean canPlayerUse(PlayerEntity player) {
		return world != null
				&& world.getBlockEntity(pos) == this
				&& player.squaredDistanceTo(
						pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5) <= 64.0;
	}

	// ------------------------------------------------------------------ persistence

	@Override
	protected void writeNbt(NbtCompound nbt, RegistryWrapper.WrapperLookup registries) {
		super.writeNbt(nbt, registries);
		Inventories.writeNbt(nbt, inventory, registries);
		nbt.putInt("heat", heat);
		nbt.putInt("progress", progress);
	}

	@Override
	protected void readNbt(NbtCompound nbt, RegistryWrapper.WrapperLookup registries) {
		super.readNbt(nbt, registries);
		Inventories.readNbt(nbt, inventory, registries);
		heat = nbt.getInt("heat");
		progress = nbt.getInt("progress");
	}

	// ------------------------------------------------------------------ screen

	@Override
	public Text getDisplayName() {
		return Text.translatable("block.uraniummod.centrifuge");
	}

	@Override
	public BlockPos getScreenOpeningData(ServerPlayerEntity player) {
		return pos;
	}

	@Override
	public ScreenHandler createMenu(int syncId, PlayerInventory playerInventory, PlayerEntity player) {
		return new CentrifugeScreenHandler(syncId, playerInventory, this, propertyDelegate);
	}
}
