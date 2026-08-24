package net.pero.uraniummod.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.block.Block;
import net.minecraft.block.BlockRenderType;
import net.minecraft.block.BlockState;
import net.minecraft.block.InventoryProvider;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.inventory.SidedInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.NamedScreenHandlerFactory;
import net.minecraft.state.StateManager;
import net.minecraft.state.property.IntProperty;
import net.minecraft.util.ActionResult;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;
import net.minecraft.world.WorldAccess;
import net.minecraft.world.WorldView;
import net.pero.uraniummod.block.entity.CentrifugeBlockEntity;

/**
 * One of the seventeen filler blocks that make up the rest of the centrifuge's
 * 3x3x2 footprint. It draws nothing — the controller's renderer covers the whole
 * machine — but it occupies space, forwards interaction and hoppers to the
 * controller, and takes the whole machine down with it when broken.
 *
 * <p>The controller's position is stored in the block state as an offset rather
 * than in a block entity, so the other seventeen positions cost no tick or
 * storage overhead at all.
 */
public class CentrifugePartBlock extends Block implements InventoryProvider {
	public static final MapCodec<CentrifugePartBlock> CODEC = createCodec(CentrifugePartBlock::new);

	/** Offset from the controller, biased so it fits an unsigned property. */
	public static final IntProperty PART_X = IntProperty.of("part_x", 0, 2);
	public static final IntProperty PART_Y = IntProperty.of("part_y", 0, 1);
	public static final IntProperty PART_Z = IntProperty.of("part_z", 0, 2);

	public CentrifugePartBlock(Settings settings) {
		super(settings);
		setDefaultState(getDefaultState().with(PART_X, 1).with(PART_Y, 0).with(PART_Z, 1));
	}

	@Override
	protected MapCodec<? extends Block> getCodec() {
		return CODEC;
	}

	@Override
	protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
		builder.add(PART_X, PART_Y, PART_Z);
	}

	/** Where the controller sits, given one of its parts. */
	public static BlockPos controllerPos(BlockState state, BlockPos pos) {
		return pos.add(-(state.get(PART_X) - 1), -state.get(PART_Y), -(state.get(PART_Z) - 1));
	}

	@Override
	protected BlockRenderType getRenderType(BlockState state) {
		return BlockRenderType.INVISIBLE;
	}

	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos,
	                             PlayerEntity player, BlockHitResult hit) {
		if (!world.isClient()) {
			BlockPos controller = controllerPos(state, pos);
			if (world.getBlockEntity(controller) instanceof NamedScreenHandlerFactory factory) {
				player.openHandledScreen(factory);
			}
		}
		return ActionResult.SUCCESS;
	}

	@Override
	protected void onStateReplaced(BlockState state, World world, BlockPos pos,
	                               BlockState newState, boolean moved) {
		if (!state.isOf(newState.getBlock())) {
			CentrifugeBlock.breakStructure(world, controllerPos(state, pos), null);
		}
		super.onStateReplaced(state, world, pos, newState, moved);
	}

	@Override
	public BlockState onBreak(World world, BlockPos pos, BlockState state, PlayerEntity player) {
		CentrifugeBlock.breakStructure(world, controllerPos(state, pos), player);
		return super.onBreak(world, pos, state, player);
	}

	/** Lets hoppers on any face of the machine reach the controller's inventory. */
	@Override
	public SidedInventory getInventory(BlockState state, WorldAccess world, BlockPos pos) {
		BlockPos controller = controllerPos(state, pos);
		return world.getBlockEntity(controller) instanceof CentrifugeBlockEntity be ? be : null;
	}

	@Override
	public ItemStack getPickStack(WorldView world, BlockPos pos, BlockState state, boolean includeData) {
		return new ItemStack(ModBlocks.CENTRIFUGE);
	}
}
