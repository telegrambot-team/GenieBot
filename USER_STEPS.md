# User Steps and Bot Responses

This document describes user interactions with GenieBot, the data the user must provide, and the data the bot returns or stores
as a result. All data structures are expressed as Pydantic models with type hints.

## Data Models

```python
from pydantic import BaseModel
from typing import Optional, List, Literal, Tuple

class Contact(BaseModel):
    phone_number: str
    first_name: str
    last_name: Optional[str]

class User(BaseModel):
    id: int
    contact: Contact

class Wish(BaseModel):
    id: int
    text: str
    status: Literal['WAITING', 'IN_PROGRESS', 'DONE']
    owner_id: int
    fulfiller_id: Optional[int] = None

class WishList(BaseModel):
    wishes: List[Wish]

class WishCreate(BaseModel):
    text: str

class TakeWish(BaseModel):
    wish_id: int

class ProofSubmission(BaseModel):
    wish_id: int
    proof: str  # file_id or message text

class WishStatistics(BaseModel):
    users: int
    wishes: int
    fulfilled: int
    top_creators: List[Tuple[int, int]]
    top_fulfillers: List[Tuple[int, int]]
```

## 1. Registration

| Step | State | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- | --- |
| Start bot | `awaiting_contact` | None | Greets the user and asks for contact information | None |
| Provide contact | `main_menu` | `Contact` | Registers the user and shows the main menu | `User` |

## 2. Main Menu Options

From the main menu users can choose various actions:

| Action | State | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- | --- |
| Make a wish | `MAKE_WISH` | `WishCreate` | Confirms wish creation and returns to main menu | `Wish` |
| View "My Wishes" | `main_menu` | None | Sends list of user's wishes | `WishList` |
| View "Wishes in Progress" | `main_menu` | None | Sends list of wishes being fulfilled | `WishList` |
| View "Fulfilled Wishes" | `main_menu` | None | Sends list of completed wishes | `WishList` |

## 3. Wish Fulfillment Flow

| Step | State | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- | --- |
| Take a wish to fulfill | `WAITING_FOR_PROOF` | `TakeWish` | Marks wish as `IN_PROGRESS`, sets state to `WAITING_FOR_PROOF`, and provides instructions | Updated `Wish` |
| Submit proof | `WAITING_FOR_PROOF` | `ProofSubmission` | Marks wish as `DONE` and thanks user | Updated `Wish` |

## 4. Admin Commands and Error Handling

### Admin Commands

Admins can use additional actions:

- `/dropwish <chat_id>:<index>` removes a specific wish.
- The "Админ: список всех желаний" button lists all fulfilled wishes and forwards proof messages.
- The "Админ: статистика" button sends overall counts and top contributor summaries.

### Error Handling

- Unrecognized messages invoke the default handler, prompting the user with guidance.
- Unexpected errors are caught by `ups_handler`, which logs the issue, notifies admins, and informs the user with a generic error message.

| Action | State | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- | --- |
| Unrecognized message | Any | Unsupported text or media | Sends default help message | None |
| Admin: list all wishes | `main_menu` | None | Sends list of all fulfilled wishes and proofs | `WishList` |
| Admin: statistics | `main_menu` | None | Sends user counts, wish totals, and top users | `WishStatistics` |
| Admin: drop wish | `main_menu` | Command parameters | Removes specified wish | Updated `Wish` |
| Internal error | Any | N/A | Sends generic error message and notifies admins | None |
