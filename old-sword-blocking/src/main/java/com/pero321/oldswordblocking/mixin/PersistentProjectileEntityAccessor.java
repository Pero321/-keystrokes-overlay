package com.pero321.oldswordblocking.mixin;

import net.minecraft.entity.projectile.PersistentProjectileEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/**
 * {@code isInGround} is protected, and whether a projectile has landed is the one thing both the
 * flight streak and the landing marks need to know.
 */
@Mixin(PersistentProjectileEntity.class)
public interface PersistentProjectileEntityAccessor {

    @Invoker("isInGround")
    boolean oldswordblocking$isInGround();
}
