"""
Bootstrap script: Create the first admin user from environment variables.

Usage:
    uv run python -m commands.create_admin

Reads from environment:
    ACM_ADMIN_EMAIL    - Admin email address
    ACM_ADMIN_USERNAME - Admin username
    ACM_ADMIN_PASSWORD - Admin initial password

Also assigns all existing unowned records (sources, notebooks, acm_items,
acm_registers) to the admin user.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from loguru import logger  # noqa: E402


async def create_admin_user():
    # Import after dotenv so DB connection works
    from api.auth_service import (
        assign_legacy_data_to_admin,
        create_user,
        get_user_by_email,
        validate_password_strength,
    )

    email = os.environ.get("ACM_ADMIN_EMAIL")
    username = os.environ.get("ACM_ADMIN_USERNAME", "admin")
    password = os.environ.get("ACM_ADMIN_PASSWORD")

    if not email or not password:
        logger.error(
            "ACM_ADMIN_EMAIL and ACM_ADMIN_PASSWORD must be set in .env"
        )
        sys.exit(1)

    # Check if admin already exists
    existing = await get_user_by_email(email)
    if existing:
        logger.info(f"Admin user already exists: {email} (id: {existing['id']})")
        return existing

    # Validate password
    valid, msg = validate_password_strength(password)
    if not valid:
        logger.error(f"Password validation failed: {msg}")
        sys.exit(1)

    # Create admin
    user = await create_user(
        email=email,
        username=username,
        password=password,
        role="admin",
        name=username.capitalize(),
    )
    logger.info(f"Admin user created: {email} (id: {user['id']})")

    # Assign legacy data
    count = await assign_legacy_data_to_admin(user["id"])
    if count > 0:
        logger.info(f"Assigned {count} existing records to admin user")

    return user


def main():
    result = asyncio.run(create_admin_user())
    print(f"\nAdmin user ready: {result['email']} (id: {result['id']})")
    print("You can now login at /login with these credentials.")


if __name__ == "__main__":
    main()
