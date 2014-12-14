LoanInvestor
===========

Unoffical LendingClub and P2P-Picks API library. Provides wrapper functions to all available API endpoints.

## lendingclub.py
Wrapper for the LendingClub API. The `API` object needs your LendingClub api key and investor id. A usage example can be found in the `main()` function.

## p2ppicks.py
Wrapper for the P2P-Picks API. The `API` object needs your P2P-Picks api key, secret, and session id. A usage example can be found in the `main()` function.

## autoinvestor.py
Automated LendingClub loan ordering tool using P2P-Picks for underwriting. The `AutoInvestor` class requires a `secrets.json` file in the working directory to specify api keys and secrets. This file should be run shortly before new loans are listed (6:00, 10:00, 14:00, 18:00 PST).

### secrets.json

This file is required for sensitive account information.
It should be a simple JSON object as follows

```
{
  "lc_api_key": "aajsufh8fhaio8i3jrh",
  "lc_investor_id": 13748291,
  "lc_portfolio": "MyPortfolio", // Name of LendingClub portfolio to use
  "p2p_key": "21BF45C43EEFA",
  "p2p_secret": "ED559A9BA392B",
  "p2p_sid": "45FB37D4AAB45B4E"
}
```
