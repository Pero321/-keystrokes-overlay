package net.pero.uraniummod.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.block.Block;
import net.minecraft.block.BlockRenderType;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.block.entity.BlockEntityTicker;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemPlacementContext;
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

	@Override
	public BlockState getPlacementState(ItemPlacementContext ctx) {
		return getDefaultState().with(FACING, ctx.getHorizontalPlayerFacing().getOpposite());
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
		}
		super.onStateReplaced(state, world, pos, newState, moved);
	}

	/** Where the tower vents, in pixels, matching CentrifugeBlockEntityRenderer. */
	private static final double VENT_Y = 15.2 / 16.0;
	private static final double COLLAR_R = 6.6 / 16.0;

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
			world.addParticle(ParticleTypes.SMOKE,
					pos.getX() + 0.5 + (random.nextDouble() - 0.5) * 0.22,
					pos.getY() + VENT_Y,
					pos.getZ() + 0.5 + (random.nextDouble() - 0.5) * 0.22,
					0.0, 0.02 + random.nextDouble() * 0.025, 0.0);
		}

		// the odd spark thrown off the collar seam
		if (random.nextDouble() < 0.15) {
			double a = random.nextDouble() * Math.PI * 2.0;
			world.addParticle(ParticleTypes.ELECTRIC_SPARK,
					pos.getX() + 0.5 + Math.cos(a) * COLLAR_R,
					pos.getY() + (11.5 + random.nextDouble() * 2.0) / 16.0,
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
