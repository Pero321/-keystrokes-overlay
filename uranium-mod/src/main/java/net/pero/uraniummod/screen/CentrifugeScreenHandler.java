package net.pero.uraniummod.screen;

import net.minecraft.block.entity.BlockEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.Inventory;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.ArrayPropertyDelegate;
import net.minecraft.screen.PropertyDelegate;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.screen.slot.Slot;
import net.minecraft.util.math.BlockPos;
import net.pero.uraniummod.block.entity.CentrifugeBlockEntity;
import net.pero.uraniummod.item.ModItems;

public class CentrifugeScreenHandler extends ScreenHandler {
	private final Inventory inventory;
	private final PropertyDelegate propertyDelegate;

	/** Client-side constructor: the block entity is already synced, so read it back from the world. */
	public CentrifugeScreenHandler(int syncId, PlayerInventory playerInventory, BlockPos pos) {
		this(syncId, playerInventory, resolveInventory(playerInventory, pos),
				new ArrayPropertyDelegate(CentrifugeBlockEntity.PROP_COUNT));
	}

	public CentrifugeScreenHandler(int syncId, PlayerInventory playerInventory,
	                               Inventory inventory, PropertyDelegate propertyDelegate) {
		super(ModScreenHandlers.CENTRIFUGE, syncId);
		checkSize(inventory, 2);
		this.inventory = inventory;
		this.propertyDelegate = propertyDelegate;
		inventory.onOpen(playerInventory.player);

		addSlot(new Slot(inventory, CentrifugeBlockEntity.INPUT_SLOT, 56, 35) {
			@Override
			public boolean canInsert(ItemStack stack) {
				return stack.isOf(ModItems.RAW_URANIUM);
			}
		});
		addSlot(new Slot(inventory, CentrifugeBlockEntity.OUTPUT_SLOT, 116, 35) {
			@Override
			public boolean canInsert(ItemStack stack) {
				return false;
			}
		});

		for (int row = 0; row < 3; row++) {
			for (int col = 0; col < 9; col++) {
				addSlot(new Slot(playerInventory, col + row * 9 + 9, 8 + col * 18, 84 + row * 18));
			}
		}
		for (int col = 0; col < 9; col++) {
			addSlot(new Slot(playerInventory, col, 8 + col * 18, 142));
		}

		addProperties(propertyDelegate);
	}

	private static Inventory resolveInventory(PlayerInventory playerInventory, BlockPos pos) {
		BlockEntity be = playerInventory.player.getWorld().getBlockEntity(pos);
		return be instanceof Inventory inv ? inv : new SimpleInventory(2);
	}

	// ------------------------------------------------------------------ gauges

	public int getHeat() {
		return propertyDelegate.get(CentrifugeBlockEntity.PROP_HEAT);
	}

	public int getMaxHeat() {
		int max = propertyDelegate.get(CentrifugeBlockEntity.PROP_MAX_HEAT);
		return max == 0 ? CentrifugeBlockEntity.MAX_HEAT : max;
	}

	public boolean isHotEnough() {
		return getHeat() >= propertyDelegate.get(CentrifugeBlockEntity.PROP_OPERATING_HEAT);
	}

	/** Height in pixels of the filled part of the heat gauge. */
	public int getHeatScaled(int pixels) {
		return getHeat() * pixels / getMaxHeat();
	}

	/** Width in pixels of the filled part of the progress arrow. */
	public int getProgressScaled(int pixels) {
		int progress = propertyDelegate.get(CentrifugeBlockEntity.PROP_PROGRESS);
		int total = propertyDelegate.get(CentrifugeBlockEntity.PROP_PROCESS_TIME);
		return total == 0 ? 0 : progress * pixels / total;
	}

	// ------------------------------------------------------------------ plumbing

	@Override
	public boolean canUse(PlayerEntity player) {
		return inventory.canPlayerUse(player);
	}

	@Override
	public ItemStack quickMove(PlayerEntity player, int slotIndex) {
		ItemStack newStack = ItemStack.EMPTY;
		Slot slot = slots.get(slotIndex);
		if (slot == null || !slot.hasStack()) {
			return newStack;
		}

		ItemStack originalStack = slot.getStack();
		newStack = originalStack.copy();

		int inventoryStart = 2;
		int inventoryEnd = slots.size();

		if (slotIndex < inventoryStart) {
			// machine -> player
			if (!insertItem(originalStack, inventoryStart, inventoryEnd, true)) {
				return ItemStack.EMPTY;
			}
			slot.onQuickTransfer(originalStack, newStack);
		} else if (!insertItem(originalStack, 0, 1, false)) {
			// player -> machine input, else shuffle within the player's own inventory
			int hotbarStart = inventoryEnd - 9;
			if (slotIndex < hotbarStart) {
				if (!insertItem(originalStack, hotbarStart, inventoryEnd, false)) {
					return ItemStack.EMPTY;
				}
			} else if (!insertItem(originalStack, inventoryStart, hotbarStart, false)) {
				return ItemStack.EMPTY;
			}
		}

		if (originalStack.isEmpty()) {
			slot.setStack(ItemStack.EMPTY);
		} else {
			slot.markDirty();
		}
		if (originalStack.getCount() == newStack.getCount()) {
			return ItemStack.EMPTY;
		}
		slot.onTakeItem(player, originalStack);
		return newStack;
	}

	@Override
	public void onClosed(PlayerEntity player) {
		super.onClosed(player);
		inventory.onClose(player);
	}
}
