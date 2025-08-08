# GenieBot - A Telegram Bot for Fulfilling Wishes 🧞‍♂️

GenieBot is a Telegram bot that enables users to create and fulfill wishes in a community-driven way. It manages a wish-granting ecosystem where users can both submit their wishes and help fulfill others' wishes.

## Core Components

### 1. Base Handlers (`base_handlers.py`)
- **Start Handler**: Initiates bot interaction and user registration
- **Contact Handler**: Manages user contact information collection
- **Default Handler**: Provides fallback responses
- **Admin Functions**: Restricted handlers for administrative tasks
- **Main UI Handler**: Manages the main menu interface

### 2. Button Handlers (`button_handlers.py`)
- **Wish Creation**: Handles the creation of new wishes
- **Wish Selection**: Manages the process of users selecting wishes to fulfill
- **Wish Fulfillment**: Processes wish completion and proof submission
- **List Management**: Handles various wish listing functionalities
  - My Wishes
  - Wishes in Progress
  - Fulfilled Wishes

### 3. Database Persistence (`db_persistence.py`)
- **Data Storage**: Manages persistent storage of:
  - User Data
  - Chat Data
  - Bot Data
  - Conversation States
- **Session Management**: Handles database connections and transactions

### 4. Configuration (`config.py`)
- **Environment Management**: Handles environment variables and configuration
- **Bot Data Structure**: Defines core data structures
  - Config class for bot configuration
  - BotData class for wish management

### 5. Constants (`constants.py`)
- **Message Templates**: Pre-defined bot responses
- **Button Labels**: UI element text
- **State Constants**: System state definitions
- **Limits**: System constraints (e.g., WISHES_TO_SHOW_LIMIT)

## Workflow States

### Wish Status
1. `WAITING`: Newly created wishes
2. `IN_PROGRESS`: Wishes being fulfilled
3. `DONE`: Completed wishes
4. `REMOVED`: Deleted wishes

### Conversation States
- `MAKE_WISH`: Active wish creation state
- `WAITING_FOR_PROOF`: Awaiting fulfillment proof
