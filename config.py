APP_TOKEN: str
APP_OWNER_ID: int

MONGO_URI: str

START_TIME_TIMESTAMP: int
END_TIME_TIMESTAMP: int

EVENTS_CHANNEL_ID: int
# Logs channel can be a text channel ID or a thread ID
LOGS_CHANNEL_ID: int

COUNCIL_ROLE: int
COMM_WIZARD_ROLE: int
HUNT_CHAMPION_ROLE: int

# This is an example of what this dictionary should look like, with values from an old Dyno Hunt
# The final/decoding hint must have the key of "-1"
# The "code" key is optional
KEYS = {
    "1": {
        "clue": "Sometimes a lot of people find a message really funny. When this happens, this is where it usually ends up.",
        "value": "sixstars",
        "code": "OIQI",
    },
    "2": {
        "clue": "You found the first key! Here’s your next clue: Recent news reports revealed that Dave has become an astronaut! A picture of him in outer space was shared. If you find it, you may be able to find the next key!",
        "value": "intergalacticdave",
        "code": "CWC",
    },
    "3": {
        "clue": "Great job getting this far! Now, you must look for something–or perhaps some people–that have proven to be quite exceptional within our community. Some might even say they are out of this world!",
        "value": "verytalkative",
        "code": "YWKW",
    },
    "4": {
        "clue": "You’re really getting the hang of this! Moderating your server is really important in order to ensure it’s a safe place for everyone. One aspect of moderating also includes banning users who violate the server’s rules, but sometimes, moderators don’t really know how to use the command. Where would you go in order to show them the documentation of the command?",
        "value": "rulebreaker",
        "code": "WZOFR",
    },
    "5": {
        "clue": "Onto the next clue… Our resident banana enthusiast is responsible for overseeing the entire Dyno Community Staff team. It’s a tall order, but he still manages to sneak away and spend some time relaxing and playing some games. ",
        "value": "pumpkinthecat",
        "code": "WITEAEJ",
    },
    "6": {
        "clue": "You’re halfway there! We love seeing people motivated to offer Dyno support! If you were interested in helping out, you’d need to find out the proper way to do so.",
        "value": "answeringquestions",
        "code": "OW",
    },
    "7": {
        "clue": "Custom Commands are really cool and powerful when used right, but if you aren’t familiar with them yet, you may want to find a page with some examples created by some users from our community!",
        "value": "coolcommands",
        "code": "YIBI",
    },
    "8": {
        "clue": "While we mostly provide support with Dyno, many are also interested in developing our applications or bots and are looking for a place to ask for help with that.",
        "value": "hackerman",
        "code": "HITC",
    },
    "9": {
        "clue": "Our server mascot has taken on a personality of his own, and you must know about him to understand much of the lore and jokes from our server!",
        "value": "dynosaur",
        "code": "DB",
    },
    "10": {
        "clue": "Woohoo! You’ve reached the last clue! Our staff team worked very hard to put together this hunt as well as all of our community events. They can be recognized on this page.",
        "value": "superstaff",
        "code": "YXQ",
    },
    "-1": {
        "clue": "You’ve successfully found all of the keys! Now for the extra challenging part: You must decode and unscramble the **9** encoded words given to you in previous messages. You’ll need to decode them using this: `VIGENERE`. Once you’re done, DM Dave the decoded message.",
    },
}
