use anchor_lang::prelude::*;
use anchor_lang::system_program::{self, Transfer};

declare_id!("2L2savqgibmLNmumGDkwDPUwzAXbJeBULRZwV6oyWfAN");

#[program]
pub mod ai_coliseum {
    use super::*;

    pub fn initialize_vault(ctx: Context<InitializeVault>) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        vault.authority = *ctx.accounts.authority.key;
        vault.total_staked = 0;
        vault.bump = ctx.bumps.vault;
        Ok(())
    }

    pub fn stake(ctx: Context<Stake>, amount: u64) -> Result<()> {
        require!(amount > 0, ErrorCode::InvalidStakeAmount);

        let user_stake = &mut ctx.accounts.user_stake;

        if user_stake.owner == Pubkey::default() {
            user_stake.owner = *ctx.accounts.user.key;
        } else {
            require_keys_eq!(
                user_stake.owner,
                *ctx.accounts.user.key,
                ErrorCode::StakeAccountOwnerMismatch
            );
        }
        
        // Transfer SOL from user to vault
        let cpi_context = CpiContext::new(
            ctx.accounts.system_program.key(),
            Transfer {
                from: ctx.accounts.user.to_account_info(),
                to: ctx.accounts.vault.to_account_info(),
            },
        );
        system_program::transfer(cpi_context, amount)?;

        user_stake.amount = user_stake
            .amount
            .checked_add(amount)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        ctx.accounts.vault.total_staked = ctx
            .accounts
            .vault
            .total_staked
            .checked_add(amount)
            .ok_or(ErrorCode::ArithmeticOverflow)?;

        Ok(())
    }

    pub fn claim_rewards(ctx: Context<ClaimRewards>, amount: u64) -> Result<()> {
        // Only vault authority (Coliseum Backend) can authorize claims
        require_keys_eq!(
            ctx.accounts.vault.authority,
            *ctx.accounts.authority.key,
            ErrorCode::Unauthorized
        );

        // Transfer SOL from vault to user
        **ctx.accounts.vault.to_account_info().try_borrow_mut_lamports()? -= amount;
        **ctx.accounts.user.to_account_info().try_borrow_mut_lamports()? += amount;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeVault<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + 32 + 8 + 1,
        seeds = [b"vault"],
        bump
    )]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Stake<'info> {
    #[account(mut, seeds = [b"vault"], bump = vault.bump)]
    pub vault: Account<'info, Vault>,
    #[account(
        init_if_needed,
        payer = user,
        space = 8 + 32 + 8,
        seeds = [b"stake", user.key().as_ref()],
        bump
    )]
    pub user_stake: Account<'info, UserStake>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ClaimRewards<'info> {
    #[account(mut, seeds = [b"vault"], bump = vault.bump)]
    pub vault: Account<'info, Vault>,
    /// CHECK: This account only receives lamports; authority checks gate the transfer.
    #[account(mut)]
    pub user: AccountInfo<'info>,
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Vault {
    pub authority: Pubkey,
    pub total_staked: u64,
    pub bump: u8,
}

#[account]
pub struct UserStake {
    pub owner: Pubkey,
    pub amount: u64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Unauthorized access to vault.")]
    Unauthorized,
    #[msg("Stake amount must be greater than zero.")]
    InvalidStakeAmount,
    #[msg("Stake account owner does not match signer.")]
    StakeAccountOwnerMismatch,
    #[msg("Arithmetic overflow.")]
    ArithmeticOverflow,
}
