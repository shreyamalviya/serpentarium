import logging
from pathlib import Path

import pytest

from serpentarium import PluginLoader
from tests.logging_utils import get_logger_config_callback

PLUGIN_DIR = Path(__file__).parent / "plugins"
MY_PARAM = "test_param"


@pytest.fixture
def plugin_loader() -> PluginLoader:
    return PluginLoader(PLUGIN_DIR)


def test_plugin_isolation(plugin_loader: PluginLoader):
    plugin1 = plugin_loader.load(plugin_name="plugin1")
    plugin2 = plugin_loader.load(plugin_name="plugin2")

    assert "Tweedledee" in plugin1.run()
    assert "Tweedledum" in plugin2.run()

    # Run again to ensure plugin2 didn't overwrite plugin1's imports
    assert "Tweedledee" in plugin1.run()
    assert "Tweedledum" in plugin2.run()


def test_module_not_found_incorrect_plugin_name(plugin_loader: PluginLoader):
    with pytest.raises(ModuleNotFoundError):
        plugin = plugin_loader.load(plugin_name="NONEXISTANT")
        plugin.run()


def test_constructor_parameters(plugin_loader: PluginLoader):
    plugin1 = plugin_loader.load(plugin_name="constructor_parameters", my_param=MY_PARAM)

    return_value = plugin1.run()

    assert return_value == MY_PARAM


def test_run_parameters(plugin_loader: PluginLoader):
    plugin1 = plugin_loader.load(plugin_name="run_parameters")

    return_value = plugin1.run(my_param=MY_PARAM)

    assert return_value == MY_PARAM


def test_multiprocessing_plugin_isolation(plugin_loader: PluginLoader):
    """
    NOTE: This test fails with the following error message:
            def dump(obj, file, protocol=None):
            '''Replacement for pickle.dump() using ForkingPickler.'''
    >       ForkingPickler(file, protocol).dump(obj)
    E       _pickle.PicklingError: Can't pickle <class 'serpentarium.multiprocessing_plugin.MultiprocessingPlugin'>: it's not the same object as serpentarium.multiprocessing_plugin.MultiprocessingPlugin

    Manual testing passes. This will need more investigating to get it to pass as an automated test
    """
    plugin1 = plugin_loader.load_multiprocessing_plugin(plugin_name="plugin1")
    plugin2 = plugin_loader.load_multiprocessing_plugin(plugin_name="plugin2")

    assert "Tweedledee" in plugin1.run()
    assert "Tweedledum" in plugin2.run()


LOG_MESSAGES = [
    (logging.DEBUG, "log1"),
    (logging.INFO, "log2"),
    (logging.WARNING, "log3"),
]


def test_child_process_logger_configuration():
    _, ipc_queue, configure_logger_fn = get_logger_config_callback()
    plugin_loader = PluginLoader(PLUGIN_DIR, configure_logger_fn)

    plugin = plugin_loader.load_multiprocessing_plugin(plugin_name="logger")
    plugin.run(log_messages=LOG_MESSAGES)

    assert not ipc_queue.empty()
    assert ipc_queue.get_nowait().msg == LOG_MESSAGES[0][1]
    assert ipc_queue.get_nowait().msg == LOG_MESSAGES[1][1]
    assert ipc_queue.get_nowait().msg == LOG_MESSAGES[2][1]
    assert ipc_queue.empty()


def test_child_process_logger_configuration__override():
    _, default_ipc_queue, default_configure_logger_fn = get_logger_config_callback()
    plugin_loader = PluginLoader(PLUGIN_DIR, default_configure_logger_fn)

    _, override_ipc_queue, override_configure_logger_fn = get_logger_config_callback()

    plugin = plugin_loader.load_multiprocessing_plugin(
        plugin_name="logger", configure_child_process_logger=override_configure_logger_fn
    )
    plugin.run(log_messages=LOG_MESSAGES)

    assert default_ipc_queue.empty()
    assert not override_ipc_queue.empty()
    assert override_ipc_queue.get_nowait().msg == LOG_MESSAGES[0][1]
    assert override_ipc_queue.get_nowait().msg == LOG_MESSAGES[1][1]
    assert override_ipc_queue.get_nowait().msg == LOG_MESSAGES[2][1]
    assert override_ipc_queue.empty()
