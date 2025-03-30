from time import time
from typing import Any, Optional

import config
import errors

from bot import DynoHunt


class DB:
    """Class for handling database operations."""

    @staticmethod
    async def insert(bot: DynoHunt, collection: str, document: dict) -> Optional[dict]:
        """Insert a document into the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            document (dict): The document to insert.

        Returns:
            dict: The inserted document.
        """
        try:
            await bot.db["prod"][collection].insert_one(document)
            return document
        except Exception as e:
            raise errors.Error(f"Failed to insert document: {e}") from e

    @staticmethod
    async def get(
        bot: DynoHunt, collection: str, collection_id: str, field: Optional[str] = None
    ) -> Optional[dict]:
        """Get a document from the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            collection_id (str): The collection ID.
            field (str, optional): The field to return. Defaults to None.

        Returns:
            dict: The document.
        """
        if field:
            document = await bot.db["prod"][collection].find_one(
                {"_id": str(collection_id)}
            )
            keys = field.split(".")
            value = document
            for key in keys:
                try:
                    value = value.get(key, None)
                except AttributeError:
                    value = None
                if value is None:
                    break
            return value
        return await bot.db["prod"][collection].find_one({"_id": str(collection_id)})

    @staticmethod
    async def get_many(
        bot: DynoHunt, collection: str, ids: Optional[list[str]] = None
    ) -> list[Optional[dict]]:
        """Get multiple documents from the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            ids (list, optional): The collection IDs. Defaults to None.

        Returns:
            list: The documents.
        """
        if not ids:
            return await bot.db["prod"][collection].find().to_list(None)
        return (
            await bot.db["prod"][collection].find({"_id": {"$in": ids}}).to_list(None)
        )

    @staticmethod
    async def update(
        bot: DynoHunt,
        collection: str,
        collection_id: str,
        update_query: dict,
        *,
        upsert: Optional[bool] = False,
    ) -> Optional[dict]:
        """Update a document in the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            collection_id (str): The collection ID.
            update_query (dict): The update query.
            upsert (bool, optional): Whether to upsert the document. Defaults to False.

        Returns:
            None
        """
        await bot.db["prod"][collection].update_one(
            {"_id": str(collection_id)}, update_query, upsert=upsert
        )
        return await DB.get(bot, collection, collection_id)

    @staticmethod
    async def set_field(
        bot: DynoHunt, collection: str, collection_id: str, field: str, value: Any
    ) -> dict:
        """Set a field in the database. Always upserts.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            collection_id (str): The collection ID.
            field (str): The field to set.
            value (Any): The value to set.

        Returns:
            dict: The updated document.
        """
        return await DB.update(
            bot, collection, collection_id, {"$set": {field: value}}, upsert=True
        )

    @staticmethod
    async def increment(
        bot: DynoHunt,
        collection: str,
        collection_id: str,
        field: str,
        *,
        value: Optional[int] = 1,
        upsert: Optional[bool] = False,
    ) -> dict:
        """Increment a field in the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            collection_id (str): The collection ID.
            field (str): The field to increment.
            value (int): The value to increment by. Defaults to 1.
            upsert (bool, optional): Whether to upsert the document. Defaults to False.

        Returns:
            dict: The updated document.
        """
        return await DB.update(
            bot, collection, collection_id, {"$inc": {field: int(value)}}, upsert=upsert
        )

    @staticmethod
    async def unset(
        bot: DynoHunt, collection: str, collection_id: str, field: str
    ) -> dict:
        """Unset a field in the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            collection_id (str): The collection ID.
            field (str): The field to unset.

        Returns:
            dict: The updated document.
        """
        return await DB.update(bot, collection, collection_id, {"$unset": {field: ""}})

    @staticmethod
    async def delete(bot: DynoHunt, collection: str, collection_id: str) -> None:
        """Delete a document from the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            collection_id (str): The collection ID.

        Returns:
            None
        """
        await bot.db["prod"][collection].delete_one({"_id": str(collection_id)})

    @staticmethod
    async def delete_many(bot: DynoHunt, collection: str, ids: list[str]) -> None:
        """Delete multiple documents from the database.

        Args:
            bot (DynoHunt): The bot instance.
            collection (str): The name of the collection. Example: "users".
            ids (list): The collection IDs.

        Returns:
            None
        """
        await bot.db["prod"][collection].delete_many({"_id": {"$in": ids}})


class User:
    """Class for handling user operations."""

    @staticmethod
    async def get_user(bot: DynoHunt, user_id: int) -> Optional[dict]:
        """Get a user's data.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            dict: The user data if found.
        """
        return await DB.get(bot, "users", str(user_id))

    @staticmethod
    async def create_user(bot: DynoHunt, user_id: int) -> dict:
        """Create a new user.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            dict: The new user data.
        """
        user_data = {
            "_id": str(user_id),
            "created_at": int(time()),
            "key_to_find": 1,
            "total_attempts": 0,
            "wrong_order_correct_guesses": 0,
            "key_completion_timestamps": {},
            "completed": False,
            "flagged": False,
        }
        return await DB.insert(bot, "users", user_data)

    @staticmethod
    async def delete_user(bot: DynoHunt, user_id: int) -> None:
        """Delete a user.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.
        """
        await DB.delete(bot, "users", str(user_id))

    @staticmethod
    async def advance_user(bot: DynoHunt, user_id: int) -> dict:
        """Advance the user to the next key.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            dict: The updated user data.
        """
        user = await User.get_user(bot, user_id)
        if not user:
            user = await User.create_user(bot, user_id)

        # This only happens when the Hunt Champion role is assigned
        if user["key_to_find"] == -1:
            user["completed"] = True
            user["key_completion_timestamps"]["-1"] = int(time())
            return await DB.update(bot, "users", str(user_id), {"$set": user})

        user["key_completion_timestamps"][str(user["key_to_find"])] = int(time())
        if str(user["key_to_find"] + 1) not in config.KEYS.keys():
            user["key_to_find"] = -1
        else:
            user["key_to_find"] += 1
        return await DB.update(bot, "users", str(user_id), {"$set": user})

    @staticmethod
    async def has_finished(bot: DynoHunt, user_id: int) -> bool:
        """Check if the user has completed the hunt.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            bool: Whether the user has completed the hunt.
        """
        user = await User.get_user(bot, user_id)
        return user.get("completed", False)

    @staticmethod
    async def increment_attempts(bot: DynoHunt, user_id: int) -> int:
        """Increment the user's guess count.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            int: The updated guess count.
        """
        if not await User.get_user(bot, user_id):
            await User.create_user(bot, user_id)
        return (await DB.increment(bot, "users", str(user_id), "total_attempts")).get(
            "total_attempts", 0
        )

    @staticmethod
    async def increment_wrong_order_guesses(bot: DynoHunt, user_id: int) -> int:
        """Increment the user's wrong order guesses.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            int: The updated wrong order guesses count.
        """
        return (
            await DB.increment(
                bot, "users", str(user_id), "wrong_order_correct_guesses"
            )
        ).get("wrong_order_correct_guesses", 0)

    @staticmethod
    async def set_flag(bot: DynoHunt, user_id: int, value: bool) -> dict:
        """Set the user's flag.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.
            value (bool): The flag value.

        Returns:
            dict: The updated user data.
        """
        return await DB.set_field(bot, "users", str(user_id), "flagged", value=value)

    @staticmethod
    async def get_key(bot: DynoHunt, user_id: int) -> Optional[str]:
        """Get the user's current key.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            int: The user's current key if they haven't finished the hunt.
        """
        if await User.has_finished(bot, user_id):
            return None
        key_to_find = (await User.get_user(bot, user_id)).get("key_to_find")
        return config.KEYS.get(str(key_to_find), config.KEYS["-1"]).get("value")

    @staticmethod
    async def get_code(bot: DynoHunt, user_id: int) -> Optional[str]:
        """Get the user's current key code.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            str: The user's current key code if they haven't finished the hunt.
        """
        if await User.has_finished(bot, user_id):
            return None
        user = await User.get_user(bot, user_id)
        if user["key_to_find"] == -1:
            return config.KEYS[str(len(config.KEYS) - 1)].get("code")
        return config.KEYS.get(str(user["key_to_find"] - 1)).get("code")

    @staticmethod
    async def get_clue(bot: DynoHunt, user_id: int) -> Optional[str]:
        """Get the user's current clue.

        Args:
            bot (DynoHunt): The bot instance.
            user_id (int): The user ID.

        Returns:
            str: The user's current clue if they haven't finished the hunt or the final clue.
        """
        if await User.has_finished(bot, user_id):
            return None
        user = await User.get_user(bot, user_id)
        key = str(user["key_to_find"])
        return config.KEYS.get(key, config.KEYS["-1"]).get("clue")
