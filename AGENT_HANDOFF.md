# GrantGuard handoff

GrantGuard is a fresh repository for a GenLayer Studionet grant-evaluation market.

Target network is Studionet chain `61999` with RPC `https://studio.genlayer.com/api`.
Use only an injected EIP-1193 wallet through `window.ethereum`; never add backend signers, WalletConnect, Privy, or embedded wallets.

The contract is in `contracts/grantguard.py`. The implementation must remain fail-closed, preserve frozen rubrics, validate public evidence, require successful finality, and maintain accounting conservation.
