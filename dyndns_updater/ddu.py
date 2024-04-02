from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
from uuid import uuid4

import click
import keyring

from .constant import APP_NAME
from .constant import CONTEXT_SETTINGS
from .db import setup_db
from .models import AllInklProvider
from .models import DynDNSSetup

DB_FILE = Path(click.get_app_dir(APP_NAME, roaming=False)) / "setup_db.json"


@dataclass
class Repo:
    name: str
    uuid: UUID


pass_repo = click.make_pass_decorator(Repo)


@click.group(help="DynDNS Updater", context_settings=CONTEXT_SETTINGS)
def ddu():
    pass


@ddu.command
def list():
    with setup_db(DB_FILE) as s:
        for setup in s.setups:
            click.echo(setup.name)
            click.echo(f"  |-> UUID: {setup.uuid}")
            click.echo(f"  |-> Provider: {setup.provider.provider_type}")


@ddu.group(help="Add a new DynDNS setup")
@click.option("-n", "--name", help="Specify a name for the setup", type=str)
@click.pass_context
def add(ctx, name: str):
    ctx.obj = Repo(name=name, uuid=uuid4())


@add.command(help="Specify ALL-INKL DynDNS setup")
@click.option("-u", "--user", type=str, prompt=True, help="DDNS user")
@click.option("-p", "--password", type=str, prompt=True, hide_input=True, help="DDNS password")
@pass_repo
def all_inkl(repo: Repo, user: str, password: str):
    setup = DynDNSSetup(name=repo.name, uuid=str(repo.uuid), provider=AllInklProvider())
    keyring.set_password(f"ddns_{setup.uuid}", user, password)
    with setup_db(DB_FILE) as s:
        s.setups.append(setup)
