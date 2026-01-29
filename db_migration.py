import argparse
import os
import subprocess
import sys

from db_backup import create_backup, cleanup_old_backups
from src.schemas.common import EnvType


def run_alembic_command(command: list, env: str) -> int:
    """Run an Alembic command with a proper environment setup.

    Args:
        command: Alembic command and arguments
        env: Environment name

    Returns:
        Return code from the Alembic command
    """
    os.environ["ENV_NAME"] = env
    full_command = [sys.executable, "-m", "alembic"] + command

    result = subprocess.run(full_command, cwd=os.path.dirname(__file__) or ".")
    return result.returncode


def migrate_postgres_up(env: str, revision: str = "head", backup: bool = True):
    """Run PostgreSQL migrations up to a specific revision.

    Args:
        env: Environment name
        revision: Target revision (default: "head" for latest)
        backup: Whether to create a backup before migrating
    """
    if backup:
        print("Creating backup before migration...")
        try:
            create_backup()
            cleanup_old_backups(keep=10)
        except Exception as e:
            print(f"Warning: Backup failed: {e}")
            response = input("Continue without backup? (y/N): ")
            if response.lower() != "y":
                print("Migration cancelled.")
                return

    print(f"Running migrations up to: {revision}")
    return_code = run_alembic_command(["upgrade", revision], env)

    if return_code == 0:
        print("PostgreSQL migration completed successfully.")
    else:
        print(f"Migration failed with return code: {return_code}")
        sys.exit(return_code)


def migrate_postgres_down(env: str, revision: str = "-1", backup: bool = True):
    """Run PostgreSQL migrations down to a specific revision.

    Args:
        env: Environment name
        revision: Target revision (default: "-1" for one step back)
        backup: Whether to create a backup before migrating
    """
    if backup:
        print("Creating backup before downgrade...")
        try:
            create_backup()
            cleanup_old_backups(keep=10)
        except Exception as e:
            print(f"Warning: Backup failed: {e}")
            response = input("Continue without backup? (y/N): ")
            if response.lower() != "y":
                print("Downgrade cancelled.")
                return

    print(f"Running migrations down to: {revision}")
    return_code = run_alembic_command(["downgrade", revision], env)

    if return_code == 0:
        print("PostgreSQL downgrade completed successfully.")
    else:
        print(f"Downgrade failed with return code: {return_code}")
        sys.exit(return_code)


def show_postgres_history(env: str):
    """Show migration history."""
    run_alembic_command(["history", "--verbose"], env)


def show_postgres_current(env: str):
    """Show the current migration revision."""
    run_alembic_command(["current", "--verbose"], env)


def create_postgres_migration(env: str, message: str):
    """Create a new migration file.

    Args:
        env: Environment name
        message: Migration message/description
    """
    run_alembic_command(["revision", "-m", message], env)


def migrate_db():
    parser = argparse.ArgumentParser(description="Migrate database and tables")
    parser.add_argument(
        "--env", type=str, required=True, help="[prod, stage, dev, test]"
    )
    parser.add_argument(
        "--db",
        type=str,
        choices=["postgres"],
        default="postgres",
        help="Database type to migrate (default: postgres)",
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["up", "down", "history", "current", "create"],
        default="up",
        help="Migration action (default: up)",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Target revision for up/down (default: head for up, -1 for down)",
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        help="Migration message (required for create action)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup before migration",
    )
    args = parser.parse_args()

    try:
        env = EnvType(args.env.lower())
    except ValueError as exc:
        raise ValueError(
            f"Invalid env: {args.env}. Valid values: prod, stage, dev, test"
        ) from exc

    os.environ["ENV_NAME"] = args.env.lower()

    if args.db == "postgres":
        backup = not args.no_backup

        if args.action == "up":
            revision = args.revision or "head"
            migrate_postgres_up(args.env.lower(), revision, backup)

        elif args.action == "down":
            revision = args.revision or "-1"
            migrate_postgres_down(args.env.lower(), revision, backup)

        elif args.action == "history":
            show_postgres_history(args.env.lower())

        elif args.action == "current":
            show_postgres_current(args.env.lower())

        elif args.action == "create":
            if not args.message:
                raise ValueError("--message is required for create action")
            create_postgres_migration(args.env.lower(), args.message)


if __name__ == "__main__":
    migrate_db()
