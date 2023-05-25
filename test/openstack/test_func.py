"""Functional tests."""
import os
import pathlib
import shutil
import subprocess

import openstack
import pytest

from molecule import logger
from molecule.test.conftest import change_dir_to
from molecule.util import run_command

LOG = logger.get_logger(__name__)


def is_openstack_auth() -> bool:
    """Is the openstack authentication config in place?"""

    try:
        conn = openstack.connect()
        list(conn.compute.servers())
        return True
    except Exception:
        return False


def format_result(result: subprocess.CompletedProcess):
    """Return friendly representation of completed process run."""
    return (
        f"RC: {result.returncode}\n"
        + f"STDOUT: {result.stdout}\n"
        + f"STDERR: {result.stderr}"
    )


@pytest.mark.skipif(not is_openstack_auth(), reason="Openstack authentication missing")
def test_command_init_and_test_scenario(tmp_path: pathlib.Path, DRIVER: str) -> None:
    """Verify that init scenario works."""
    shutil.rmtree(tmp_path, ignore_errors=True)
    tmp_path.mkdir(exist_ok=True)

    scenario_name = "default"

    with change_dir_to(tmp_path):
        scenario_directory = tmp_path / "molecule" / scenario_name
        cmd = [
            "molecule",
            "init",
            "scenario",
            scenario_name,
            "--driver-name",
            DRIVER,
        ]
        result = run_command(cmd)
        assert result.returncode == 0

        assert scenario_directory.exists()

        confpath = os.path.join(scenario_directory, "molecule.yml")
        testconf = os.path.join(
            os.path.dirname(__file__),
            "scenarios/molecule",
            scenario_name,
            "molecule.yml",
        )

        shutil.copyfile(testconf, confpath)

        cmd = ["molecule", "--debug", "test", "-s", scenario_name]
        result = run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skipif(not is_openstack_auth(), reason="Openstack authentication missing")
@pytest.mark.parametrize(
    "scenario",
    [("multiple"), ("security_group"), ("network"), ("volume")],
)
def test_specific_scenarios(temp_dir, scenario) -> None:
    """Verify that specific scenarios work"""
    scenario_directory = os.path.join(os.path.dirname(__file__), "scenarios")

    with change_dir_to(scenario_directory):
        cmd = ["molecule", "test", "--scenario-name", scenario]
        result = run_command(cmd)
        assert result.returncode == 0
