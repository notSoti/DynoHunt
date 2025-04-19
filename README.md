# Dyno Hunt

A Discord bot designed for managing the annual Dyno Hunt event in the [Dyno Discord server](https://discord.gg/dyno). This bot streamlines the scavenger hunt experience by providing automated key validation, progress tracking, comprehensive user statistics, and detailed activity logging.

## Features

- DM-based scavenger hunt system
- Key validation and progress tracking
- Optional, automatic logging of key attempts and completions
- Staff commands for monitoring hunt progress
- User statistics and analytics with graphs
- Hot-reload capability for faster deployment
- Automatic command tree synchronization to minimize Discord API calls
- MongoDB database

## Installation

1. Clone the repository:
```bash
git clone https://github.com/notSoti/DynoHunt.git
cd DynoHunt
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install -U -r requirements.txt
```

3. Configure the bot:
   - Copy `config.py` and update the following values:
     - `APP_TOKEN`: Your Discord bot token
     - `APP_OWNER_ID`: Your Discord user ID
     - `MONGO_URI`: Your MongoDB connection string
     - `START_TIME_TIMESTAMP` and `END_TIME_TIMESTAMP`: Unix timestamps for hunt duration
     - `KEYS`: Dictionary of clues and their answers
     - Various Discord role and channel IDs

## Configuration

### KEYS Dictionary Structure

The hunt is configured through the `KEYS` dictionary in `config.py`. Each key in the hunt is represented by a numbered entry in the dictionary, with a special `-1` key for the final clue. Here's the structure:

```python
KEYS = {
    "1": {
        "clue": "The clue text that users need to solve",
        "value": "theanswerkey",  # Should be one word
        "code": "OPTIONAL_CODE"    # Optional code to reveal upon solving
    },
    // ... more keys ...
    "-1": {
        "clue": "The final decoding instructions"
    }
}
```

Each key entry contains:
- `clue`: The text shown to users that they need to solve
- `value`: The answer they need to provide (lowercase letters only)
- `code`: (Optional) A code/token that can be revealed upon solving the key

The special `-1` key entry contains only a clue, which is shown to users after they find all other keys, containing instructions for the final decoding.

## Running the Bot

The bot supports different modes of operation through command-line arguments:

### Development Mode
```bash
python bot.py --dev --prefix !
```
- `--dev`: Runs the bot in development mode
  - Uses a separate development database environment

- `--prefix`: Sets a command prefix (e.g., `!`) for text commands
  - Only staff members (with Council or Community Wizard roles) and the application's owner can use prefix commands
  - If not set, the bot will only respond to mentions
  - Multiple prefixes can be specified: `--prefix !`

### Production Mode
```bash
python bot.py
```
- Runs without development features
- Uses the production database
- Only responds to slash commands by default

## Code Structure

```
DynoHunt/
├── bot.py              # Main bot initialization and setup
├── config.py           # Configuration and constants
├── errors.py          # Custom error definitions
├── logger.py          # Logging configuration
├── utils.py           # Database and utility functions
└── cogs/              # Bot functionality modules
    ├── discord_logger.py   # Logging user interactions
    ├── dm_handler.py       # DM-based hunt interactions
    ├── help.py            # Help command functionality
    ├── hot_reload.py      # Development hot-reload
    ├── role_handler.py    # Role-based functionality
    ├── staff_commands.py  # Admin commands
    └── user_commands.py   # User-facing commands
```

## Key Components

- **bot.py**: Core bot functionality and command tree setup
- **utils.py**: Database operations and user management
- **dm_handler.py**: Main hunt logic and key validation
- **discord_logger.py**: Optional activity logging and monitoring
- **staff_commands.py**: Administrative commands and statistics

### Automatic Tree Synchronization

The bot implements an efficient command tree synchronization system to minimize Discord API calls. Here's how it works:

1. On startup, the bot generates a SHA-256 hash of all registered commands and their properties
2. This hash is stored in a `tree.hash` file in the project root
3. On subsequent startups, a new hash is generated and compared with the stored one
4. Commands are only synced with Discord's API if the hash has changed
5. This ensures that API calls for command registration are only made when necessary

This system is particularly useful during development when you're frequently restarting the bot, as it prevents unnecessary API calls and helps avoid Discord's rate limits.

## Development

### Code Style

The project uses [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting. Ruff is a fast Python linter written in Rust that consolidates multiple Python code quality tools into a single package.

To format your code before committing:
```bash
ruff format .
```

To check for linting issues:
```bash
ruff check .
```

Ruff is configured to enforce consistent code style across the project. Make sure to run these commands before submitting a pull request.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Uses [Motor](https://github.com/mongodb/motor) for MongoDB integration
- Graphs powered by [QuickChart](https://quickchart.io/)
