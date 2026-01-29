#!/usr/bin/env python
"""Database backup script for PostgreSQL.

Creates a backup of the PostgreSQL database before migrations are performed.
Backups are stored in the `db_backups/` directory with timestamp and environment info.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.adapters.doppler import load_doppler_secrets



def get_db_config() -> dict:
    load_doppler_secrets()

    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "database": os.environ["POSTGRES_DB"],
    }


def create_backup(backup_dir: str = "db_backups") -> str:
    config = get_db_config()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    backup_file = backup_path / f"{config['database']}_{timestamp}.sql"

    env_vars = os.environ.copy()
    env_vars["PGPASSWORD"] = config["password"]

    # Build pg_dump command
    cmd = [
        "pg_dump",
        "-h", config["host"],
        "-p", config["port"],
        "-U", config["user"],
        "-d", config["database"],
        "-f", str(backup_file),
        "--no-owner",
        "--no-acl",
    ]

    print(f"Creating backup: {backup_file}")

    try:
        subprocess.run(
            cmd,
            env=env_vars,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Backup created successfully: {backup_file}")
        return str(backup_file)
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e.stderr}", file=sys.stderr)
        raise
    except FileNotFoundError:
        print(
            "pg_dump not found. Please install PostgreSQL client tools.",
            file=sys.stderr,
        )
        raise


def restore_backup(backup_file: str) -> None:
    config = get_db_config()

    env_vars = os.environ.copy()
    env_vars["PGPASSWORD"] = config["password"]

    # Build psql command
    cmd = [
        "psql",
        "-h", config["host"],
        "-p", config["port"],
        "-U", config["user"],
        "-d", config["database"],
        "-f", backup_file,
    ]

    print(f"Restoring backup: {backup_file}")

    try:
        subprocess.run(
            cmd,
            env=env_vars,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Backup restored successfully from: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e.stderr}", file=sys.stderr)
        raise


def list_backups(backup_dir: str = "db_backups") -> list:
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        return []

    return [str(bu) for bu in sorted(backup_path.glob("*.sql"), reverse=True)]


def cleanup_old_backups(backup_dir: str = "db_backups", keep: int = 20):
    """Remove old backups, keeping only the most recent ones.
    """
    backups_list = list_backups(backup_dir)

    if len(backups_list) <= keep:
        return

    to_remove = backups_list[keep:]
    for backup_file in to_remove:
        print(f"Removing old backup: {backup_file}")
        Path(backup_file).unlink()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL backup utility")
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list", "cleanup"],
        help="Action to perform",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="dev",
        help="Environment (dev, test, stage, prod)",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Backup file for restore action",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=10,
        help="Number of backups to keep for cleanup action",
    )

    args = parser.parse_args()

    os.environ.setdefault("ENV_NAME", args.env)

    if args.action == "backup":
        create_backup(args.env)
    elif args.action == "restore":
        if not args.file:
            print("--file is required for restore action", file=sys.stderr)
            sys.exit(1)

        restore_backup(args.file)
    elif args.action == "list":
        backups = list_backups()

        if backups:
            print(f"Available backups for {args.env}:")
            for b in backups:
                print(f"  {b}")
        else:
            print(f"No backups found for {args.env}")
    elif args.action == "cleanup":
        cleanup_old_backups(keep=args.keep)

