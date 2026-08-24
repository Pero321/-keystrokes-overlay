package net.pero.uraniummod.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.block.Block;
import net.minecraft.block.BlockRenderType;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.block.Blocks;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.block.entity.BlockEntityTicker;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.item.ItemStack;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.screen.NamedScreenHandlerFactory;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.state.StateManager;
import net.minecraft.state.property.BooleanProperty;
import net.minecraft.state.property.EnumProperty;
import net.minecraft.state.property.Properties;
import net.minecraft.util.ActionResult;
import net.minecraft.util.ItemScatterer;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.World;
import net.pero.uraniummod.block.entity.CentrifugeBlockEntity;
import net.pero.uraniummod.particle.ModParticles;
import net.pero.uraniummod.block.entity.ModBlockEntities;

public class CentrifugeBlock extends BlockWithEntity {
	public static final MapCodec<CentrifugeBlock> CODEC = createCodec(CentrifugeBlock::new);

	public static final EnumProperty<Direction> FACING = Properties.HORIZONTAL_FACING;
	public static final BooleanProperty LIT = Properties.LIT;

	public CentrifugeBlock(Settings settings) {
		super(settings);
		setDefaultState(getDefaultState().with(FACING, Direction.NORTH).with(LIT, false));
	}

	@Override
	protected MapCodec<? extends BlockWithEntity> getCodec() {
		return CODEC;
	}

	@Override
	protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
		builder.add(FACING, LIT);
	}

	/** The machine claims a 3x3 footprint, two blocks tall, centred on the controller. */
	public static final int RADIUS = 1;
	public static final int HEIGHT = 2;

	@Override
	public BlockState getPlacementState(ItemPlacementContext ctx) {
		if (!hasRoom(ctx.getWorld(), ctx.getBlockPos(), ctx)) {
			return null;   // cancels the placement rather than half-building it
		}
		return getDefaultState().with(FACING, ctx.getHorizontalPlayerFacing().getOpposite());
	}

	private static boolean hasRoom(World world, BlockPos origin, ItemPlacementContext ctx) {
		for (BlockPos pos : footprint(origin)) {
			if (pos.equals(origin)) {
				continue;
			}
			if (!world.getBlockState(pos).canReplace(ctx)) {
				return false;
			}
		}
		return world.isInBuildLimit(origin.up(HEIGHT - 1));
	}

	/**
	 * True if anything is powering the machine anywhere on its surface.
	 *
	 * <p>The controller sits in the middle of the bottom layer, surrounded on
	 * every side by its own parts, so asking whether the controller itself is
	 * receiving power would always answer no. Parts emit nothing, so scanning the
	 * whole footprint only ever picks up power from outside the machine.
	 */
	public static boolean isStructurePowered(World world, BlockPos controller) {
		for (BlockPos pos : footprint(controller)) {
			if (world.isReceivingRedstonePower(pos)) {
				return true;
			}
		}
		return false;
	}

	/** Every position the machine occupies, controller included. */
	public static Iterable<BlockPos> footprint(BlockPos controller) {
		return BlockPos.iterate(
				controller.add(-RADIUS, 0, -RADIUS),
				controller.add(RADIUS, HEIGHT - 1, RADIUS));
	}

	/**
	 * Builds the rest of the machine. This hangs off onBlockAdded rather than
	 * onPlaced so that /setblock and structure placement form a complete machine
	 * too, not just a controller sitting on its own.
	 */
	@Override
	protected void onBlockAdded(BlockState state, World world, BlockPos pos,
	                            BlockState oldState, boolean notify) {
		super.onBlockAdded(state, world, pos, oldState, notify);
		if (world.isClient() || oldState.isOf(this)) {
			return;
		}
		for (BlockPos part : footprint(pos)) {
			if (part.equals(pos) || !world.getBlockState(part).isReplaceable()) {
				continue;
			}
			world.setBlockState(part, ModBlocks.CENTRIFUGE_PART.getDefaultState()
					.with(CentrifugePartBlock.PART_X, part.getX() - pos.getX() + RADIUS)
					.with(CentrifugePartBlock.PART_Y, part.getY() - pos.getY())
					.with(CentrifugePartBlock.PART_Z, part.getZ() - pos.getZ() + RADIUS),
					Block.NOTIFY_ALL);
		}
	}

	/**
	 * Clears the whole machine. Called from the controller and from any part, so
	 * it has to tolerate being re-entered: each position is set to air with
	 * NOTIFY_ALL, which fires onStateReplaced on the piece being removed.
	 */
	public static void breakStructure(World world, BlockPos controller, PlayerEntity player) {
		if (world.isClient()) {
			return;
		}
		BlockState controllerState = world.getBlockState(controller);
		if (!controllerState.isOf(ModBlocks.CENTRIFUGE)) {
			// controller already gone; just sweep up any orphaned parts
			clearParts(world, controller);
			return;
		}
		if (world.getBlockEntity(controller) instanceof CentrifugeBlockEntity be) {
			ItemScatterer.spawn(world, controller, be);
			be.clear();
		}
		clearParts(world, controller);
		if (world.getBlockState(controller).isOf(ModBlocks.CENTRIFUGE)) {
			world.breakBlock(controller, player != null && !player.isCreative());
		}
	}

	private static void clearParts(World world, BlockPos controller) {
		for (BlockPos part : footprint(controller)) {
			if (part.equals(controller)) {
				continue;
			}
			if (world.getBlockState(part).isOf(ModBlocks.CENTRIFUGE_PART)) {
				world.setBlockState(part, Blocks.AIR.getDefaultState(), Block.NOTIFY_ALL);
			}
		}
	}

	@Override
	protected BlockRenderType getRenderType(BlockState state) {
		return BlockRenderType.MODEL;
	}

	@Override
	public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
		return new CentrifugeBlockEntity(pos, state);
	}

	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos,
	                             PlayerEntity player, BlockHitResult hit) {
		if (!world.isClient()) {
			if (world.getBlockEntity(pos) instanceof NamedScreenHandlerFactory factory) {
				player.openHandledScreen(factory);
			}
		}
		return ActionResult.SUCCESS;
	}

	@Override
	protected void onStateReplaced(BlockState state, World world, BlockPos pos,
	                               BlockState newState, boolean moved) {
		if (!state.isOf(newState.getBlock())) {
			if (world.getBlockEntity(pos) instanceof CentrifugeBlockEntity be) {
				ItemScatterer.spawn(world, pos, be);
			}
			clearParts(world, pos);
		}
		super.onStateReplaced(state, world, pos, newState, moved);
	}

	/** Where the tower vents, in pixels, matching CentrifugeBlockEntityRenderer. */
	private static final double VENT_Y = 31.0 / 16.0;
	private static final double COLLAR_R = 20.0 / 16.0;

	@Override
	public void randomDisplayTick(BlockState state, World world, BlockPos pos, Random random) {
		if (!state.get(LIT)) {
			return;
		}

		if (random.nextDouble() < 0.10) {
			world.playSound(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
					SoundEvents.BLOCK_BEACON_AMBIENT, SoundCategory.BLOCKS,
					0.30f, 0.5f + random.nextFloat() * 0.1f, false);
		}

		// steam off the rotor housing at the top of the tower
		for (int i = 0; i < 2; i++) {
			if (random.nextDouble() > 0.5) {
				continue;
			}
			world.addParticle(ModParticles.URANIUM_STEAM,
					pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 0.9,
					pos.getY() + VENT_Y,
					pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 0.9,
					0.0, 0.02 + random.nextDouble() * 0.03, 0.0);
		}

		// the odd spark thrown off the collar seam
		if (random.nextDouble() < 0.15) {
			double a = random.nextDouble() * Math.PI * 2.0;
			world.addParticle(ParticleTypes.ELECTRIC_SPARK,
					pos.getX() + 0.5 + Math.cos(a) * COLLAR_R,
					pos.getY() + (20.0 + random.nextDouble() * 6.0) / 16.0,
					pos.getZ() + 0.5 + Math.sin(a) * COLLAR_R,
					Math.cos(a) * 0.02, 0.01, Math.sin(a) * 0.02);
		}
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(World world, BlockState state,
	                                                             BlockEntityType<T> type) {
		return validateTicker(type, ModBlockEntities.CENTRIFUGE, CentrifugeBlockEntity::tick);
	}
}
