# Echo2
Code features
- Codebase rewritten, more modular and easier to configure
- Legacy Code removed that wasn't used (auto ping after delay)
- Channels, Users, etc are now defined using IDs and not names which is more efficient
- All commands that need perms are specified per channel and not role

General updates
- Now auto pings at 12 reacts, no more user input
- Old message clean a lot more reliable
- Message reacts can be easily disabled on messages for a cleaner role menu
- Conversation in the LFP channels is blocked by requiring a react and otherwise deleting
- Conversation in the lobby channel is blocked by requiring lobby in the message

New features
- Pinging for unofficals is now done through Echo2, auto checks 2 hour delay and time for less abuse
- Command to purge a channel (doesn't delete specified), might be useful for admins
- Hello (: