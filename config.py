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
        "clue": "Our resident banana enthusiast is responsible for overseeing the entire Dyno Community Staff team. It’s a tall order, but he still manages to sneak away and spend some time relaxing and hanging out with his cat. I still remember a beloved picture he posted in <#225182513465786369> years ago...",
        "value": "wildpumpkin",
    },
    "2": {
        "clue": "Great, you made it through the first clue! If you get stuck trying to solve the hunt, remember that every week, a new topic awaits—but before you share your thoughts, make sure you understand the right way to jump in. The answer is tucked away where consistent discussions take shape.",
        "value": "reallytalkative",
    },
    "3": {
        "clue": "Excellent, you made it to the third clue! Some people may find themselves wondering… how can they get to their Dyno dashboard? Only the smartest bot would know the answer to that one. Who could it be?",
        "value": "masterofdashboards",
    },
    "4": {
        "clue": "Running a server is one thing, but getting it noticed is another. If you want your server to stand out among many, you’ll need to check out a page that helps with just that—getting your server listed and visible!",
        "value": "listedmyserver",
    },
    "5": {
        "clue": "The wizards are hard at work, sending the questions your way. It’s a place where people often come together to share their thoughts, but be quick—don’t miss it before it closes.",
        "value": "heateddebate",
    },
    "6": {
        "clue": "You’ve mastered the art of sending messages, but what if you want to learn how to make them stand out? A little structure, a splash of color, and some formatting magic can go a long way!",
        "value": "zerowidthspace",
    },
    "7": {
        "clue": "Sometimes, a simple command can take you out of this world—literally. If you're curious about what’s orbiting above, the answer might be found in a manual that’s not quite NASA-approved.",
        "value": "futuristiccommand",
    },
    "8": {
        "clue": "Sometimes, staying in the loop means keeping an eye on what others are up to. One bot in particular wears its activity loud and proud—perhaps it's hiding something more than just a status.",
        "value": "incognitostealth",
    },
    "9": {
        "clue": "It’s where the hunt begins, and the rules are laid out for all to see. But a closer look might reveal an extra challenge waiting to be found.",
        "value": "witchhunt",
    },
    "10": {
        "clue": "Bots might run on code, but around here, even bots wear labels. One of them holds a secret—if you know where to look.",
        "value": "zestyrolename",
    },
    "11": {
        "clue": "Names can tell you a lot—but not always everything. Someone’s secretary goes by something a little different… a fun twist, perhaps. Take a closer look, and you might just find what you're looking for.",
        "value": "everyonesfavoritehelper",
    },
    "12": {
        "clue": "Change doesn’t happen out of nowhere—there’s a process to getting ideas off the ground. Read carefully; the process starts before you even type a word.",
        "value": "valuedsuggestion",
    },
    "-1": {
        "clue": "You’ve successfully found all of the keys! Now for the extra challenging part: take the first letter of each key you’ve found so far and use an Atbash cipher to figure out the secret message. Once you’ve decoded it, DM Dave your answer.",
    },
}
