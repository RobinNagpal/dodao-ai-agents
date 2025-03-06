# Save criteria info

The criteria infor can be saved at sub-industry level or industry level, or at industry group level

Reason we are allows for this is because at the starting we will be saving it at industry-group level, or at industry level.

As our platform gets refined, we can expect it to be saved at sub-industry level.


For example, for REITs, we will be adding specific criteria at the industry-group level, and not for specific REIT types for now.


# Check for criteria info
When adding a ticker, we will check if criteria info exists at the sub-industry level, if not, we will check at the industry level, and then at the industry-group level.

if its not found at any level, we will create a new criteria info at the industry-group level. (Only the top level).

The name of the file will be `criteria-info.json`

This is what the task is.
