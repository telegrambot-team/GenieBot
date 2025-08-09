# User Steps and Bot Responses

This document describes user interactions with GenieBot, the data the user must provide, and the data the bot returns or stores
as a result. All data structures are expressed as Pydantic models with type hints.

## Data Models

```python
from pydantic import BaseModel
from typing import Optional, List, Literal

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
```

## 1. Registration

| Step | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- |
| Start bot | None | Greets the user and asks for contact information | None |
| Provide contact | `Contact` | Registers the user and shows the main menu | `User` |

## 2. Main Menu Options

From the main menu users can choose various actions:

| Action | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- |
| Make a wish | `WishCreate` | Confirms wish creation and returns to main menu | `Wish` |
| View "My Wishes" | None | Sends list of user's wishes | `WishList` |
| View "Wishes in Progress" | None | Sends list of wishes being fulfilled | `WishList` |
| View "Fulfilled Wishes" | None | Sends list of completed wishes | `WishList` |

## 3. Wish Fulfillment Flow

| Step | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- |
| Take a wish to fulfill | `TakeWish` | Marks wish as `IN_PROGRESS` and provides instructions | Updated `Wish` |
| Submit proof | `ProofSubmission` | Marks wish as `DONE` and thanks user | Updated `Wish` |

## 4. Miscellaneous

| Action | Input Model | Bot Response | Output / Stored Model |
| --- | --- | --- | --- |
| Unrecognized message | Any unsupported text or media | Sends default help message | None |
| Admin command (admin users only) | Specific command or button | Executes administrative task | Depends on command |

