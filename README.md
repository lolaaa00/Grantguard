# GrantGuard

GrantGuard is a consensus-powered grant evaluation market on GenLayer Studionet.
Sponsors freeze a grant rubric and fund a round. Applicants submit proposals with public evidence. GenLayer validators independently evaluate every criterion, qualified proposals enter a challenge window, and the surviving winner receives a native-GEN award certificate.

## Network

- Studionet chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Frontend: to be deployed
- Contract: to be deployed

## Development

```bash
python3 -m pytest tests/direct -q
npm install
npm run typecheck
npm run build
```

GrantGuard is designed to fail closed on unavailable evidence, malformed consensus results, failed criteria, open challenges, and unauthorized withdrawals.
