import enum
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID
from uuid import uuid4

import click
import keyring
from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
APP_NAME = "ddu"


class DynDNSProvider(str, enum.Enum):
    ALL_INKL = enum.auto()


class AllInklProvider(BaseModel):
    provider_type: Literal[DynDNSProvider.ALL_INKL] = DynDNSProvider.ALL_INKL
    update_url: HttpUrl = Field(default=HttpUrl("https://dyndns.kasserver.com/"))


class DynDNSSetup(BaseModel):
    uuid: str
    provider: AllInklProvider = Field(discriminator="provider_type")
    name: str


class SetupDB(BaseModel):
    setups: list[DynDNSSetup]


@dataclass
class Repo:
    name: str
    uuid: UUID


pass_repo = click.make_pass_decorator(Repo)


@click.group(help="DynDNS Updater", context_settings=CONTEXT_SETTINGS)
def ddu():
    pass


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
    setup_db_file = Path(click.get_app_dir(APP_NAME, roaming=False)) / "setup_db.json"
    if setup_db_file.exists():
        if not setup_db_file.is_file():
            click.ClickException(f"Setup DB file {setup_db_file} is not a valid file")
        setup_db = SetupDB.model_validate_json(setup_db_file.read_text())
    else:
        setup_db = SetupDB(setups=[])
    setup_db.setups.append(setup)
    setup_db_file.parent.mkdir(exist_ok=True, parents=True)
    setup_db_file.write_text(setup_db.model_dump_json())
