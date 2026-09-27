# GrantGuard architecture

GrantGuard freezes the grant rubric and evidence policy on-chain, binds proposal data and public evidence to a proposal hash, evaluates proposal evidence through GenLayer consensus, opens a challenge window, and finalizes one deterministic award. The frontend is read-only with respect to verdicts: it submits transactions and reads the contract's authoritative state.
