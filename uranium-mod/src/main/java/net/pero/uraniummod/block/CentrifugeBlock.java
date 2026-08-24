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

	/** Drum centres in pixels, matching CentrifugeBlockEntityRenderer. */
	private static final float[][] DRUM_XZ = {{4.0f, 4.0f}, {12.0f, 4.0f}, {8.0f, 11.0f}};

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

		for (float[] drum : DRUM_XZ) {
			if (random.nextDouble() > 0.45) {
				continue;
			}
			double x = pos.getX() + drum[0] / 16.0 + (random.nextDouble() - 0.5) * 0.16;
			double y = pos.getY() + 14.6 / 16.0;
			double z = pos.getZ() + drum[1] / 16.0 + (random.nextDouble() - 0.5) * 0.16;
			world.addParticle(ParticleTypes.SMOKE, x, y, z,
					0.0, 0.015 + random.nextDouble() * 0.02, 0.0);
		}

		if (random.nextDouble() < 0.12) {
			float[] drum = DRUM_XZ[random.nextInt(DRUM_XZ.length)];
			world.addParticle(ParticleTypes.ELECTRIC_SPARK,
					pos.getX() + drum[0] / 16.0, pos.getY() + 14.2 / 16.0,
					pos.getZ() + drum[1] / 16.0,
					(random.nextDouble() - 0.5) * 0.02, 0.01, (random.nextDouble() - 0.5) * 0.02);
		}
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(World world, BlockState state,
	                                                             BlockEntityType<T> type) {
		return validateTicker(type, ModBlockEntities.CENTRIFUGE, CentrifugeBlockEntity::tick);
	}
}
