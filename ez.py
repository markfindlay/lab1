#!/usr/bin/env python

from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.inventory import ConnectionOptions
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_jinja2.plugins.tasks import template_file
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure
from nornir_scrapli.tasks import send_command
import ipdb
import json
from rich.console import Console
from rich.table import Table
from pprint import pprint
import argparse
import sys
import os

def get_value(haystack: list[dict], needle: str) -> dict:
    for d in haystack:
        if needle in d:
            return d[needle][0]['data']
        
def save_config_to_file(hostname: str, config: str, backup_dir: str = "backup/") -> None:
    filename = f"{hostname}.cfg"
    if not os.path.exists(backup_dir):
        os.mkdir(backup_dir)
    with open(os.path.join(backup_dir, filename), "w") as f:
        f.write(config)

def backup_task(task: Task) -> None:
    result = task.run(
        name="Backup config",
        task=napalm_get,
        getters=["get_config"],
        getters_options={
            "get_config": {
                "sanitized": False,
            }
        }
    )
    config = result.result['get_config']['running']
    save_config_to_file(task.host, config)

def restore_task(task: Task) -> None:
    task.run(
        name="Restore config",
        task=napalm_configure,
        filename=f"backup/{task.host}.cfg",
        replace=True,  
    )

def backup(nr: Nornir, args: argparse.Namespace) -> None:
    for host in nr.inventory.hosts:
        nr.inventory.hosts[host].platform = "junos"
    result = nr.run(task=backup_task)
    print_result(result)

def restore(nr: Nornir, args: argparse.Namespace) -> None:
    for host in nr.inventory.hosts:
        nr.inventory.hosts[host].platform = "junos"
    result = nr.run(task=restore_task)
    print_result(result)
    
def config(nr: Nornir, args: argparse.Namespace) -> None:
    result = nr.run(task=template_file, template="test.jinja", path="templates", )
    print_result(result)

def show_version(nr: Nornir) -> None:
    results = nr.run(task=send_command, command="show version | display json")
    table = Table(title="Command output")
    stuctured = []
    for r in results:
        json_data = json.loads(results[r].result)
        stuctured.append(json_data)
        software_version = get_value(json_data['software-information'], "junos-version")
        table.add_row(r, software_version)

    console = Console()
    console.print(table)

def show(nr: Nornir, args: argparse.Namespace) -> None:
    for host in nr.inventory.hosts:
        nr.inventory.hosts[host].platform = "juniper_junos"
        nr.inventory.hosts[host].connection_options["scrapli"] = ConnectionOptions(extras={'auth_strict_key': False})
        nr.inventory.hosts[host].connection_options["scrapli_netconf"] = ConnectionOptions(extras={'auth_strict_key': False})
    if args.command == "version":
        show_version(nr)

def run(nr: Nornir, args: argparse.Namespace):
    for host in nr.inventory.hosts:
        nr.inventory.hosts[host].platform = "juniper_junos"
        nr.inventory.hosts[host].connection_options["scrapli"] = ConnectionOptions(extras={'auth_strict_key': False})
        nr.inventory.hosts[host].connection_options["scrapli_netconf"] = ConnectionOptions(extras={'auth_strict_key': False})
    result = nr.run(task=send_command, command=args.command)
    print_result(result)

def main(args: argparse.Namespace) -> None:
    nr = InitNornir(config_file="ez.yml")
    cmds = {
        "backup": backup,
        "restore": restore,
        "config": config,
        "run": run,
        "show": show,
    }
    try:
        cmds[args.cmd](nr, args)
    except KeyError:
        print("Nothing to do")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CLI utility for easy render, deploy and backup of configuration')
    subparsers = parser.add_subparsers(title="Commands", dest="cmd")
    config_parser = subparsers.add_parser("config", help="Render and deploy config for specified devices")
    backup_parser = subparsers.add_parser("backup", help="Backup config for specified devices")
    restore_parser = subparsers.add_parser("restore", help="Restore backup config to devices")
    show_parser = subparsers.add_parser("show", help="Run predefined show commands that return structured output")
    run_parser = subparsers.add_parser("run", help="Run arbitrary show commands")

    run_parser.add_argument("command", action='store', type=str, help="Command as a string")
    show_parser.add_argument("command", choices=['version', "uptime"], help="List of supported commands. Supported choices are version, uptime", metavar='')

    args = parser.parse_args()

    main(args)