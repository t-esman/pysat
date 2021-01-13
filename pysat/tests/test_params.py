#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""
tests the pysat utils area
"""

import copy
from importlib import reload
import os
import pytest
import shutil

import pysat  # required for reimporting pysat
from pysat import params
from pysat._params import Parameters  # required for eval statements
from pysat.tests.travisci_test_class import TravisCICleanSetup


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.stored_params = copy.deepcopy(params)
        # set up default values
        params.restore_defaults()

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        params = self.stored_params
        params.store()

    #######################
    # test pysat data dir options
    def test_set_data_dirs_param_single(self):
        """Update pysat directory via params, single string input"""
        params['data_dirs'] = '.'
        assert params['data_dirs'] == ['.']

        # Check if next load of pysat remembers the change
        reload(pysat)
        assert params['data_dirs'] == ['.']

    def test_set_data_dirs_param_with_list(self):
        """Update pysat directories via pysat.params, list of strings"""
        params['data_dirs'] = ['.', './']
        assert params['data_dirs'] == ['.', './']

        # Check if next load of pysat remembers the change
        reload(pysat)
        assert params['data_dirs'] == ['.', './']

    def test_set_data_dir_wrong_path(self):
        """Update data_dir with an invalid path form"""
        with pytest.raises(ValueError):
            params['data_dirs'] = 'not_a_directory'

    def test_set_data_dir_bad_directory(self):
        """Ensure you can't set data directory to bad path"""
        with pytest.raises(ValueError) as excinfo:
            params['data_dirs'] = '/fake/directory/path'
        assert str(excinfo.value).find("don't lead to a valid") >= 0

    def test_repr(self):
        """Test __repr__ method"""
        out = params.__repr__()
        assert out.find('Parameters(path=') >= 0

    def test_str(self):
        """Ensure str method works"""
        out = str(params)
        # Confirm start of str
        assert out.find('pysat Parameters object') >= 0

        # Confirm that default, non-default, and user values present
        assert out.find('pysat settings') > 0
        assert out.find('Standard parameters:') > 0

        assert out.find('settings (non-default)') > 0
        assert out.find('Standard parameters (no defaults):') > 0

        assert out.find('user values') > 0
        assert out.find('User parameters:') > 0

    def test_restore_defaults(self):
        """Test restore_defaults works as intended"""

        # Get default value, as per setup
        default_val = params['update_files']

        # Change value to non-default
        params['update_files'] = not default_val

        # Restore defaults
        params.restore_defaults()

        # Ensure new value is the default
        assert params['update_files'] == default_val

        # make sure that non-default values left as is
        assert params['data_dirs'] != []

    def test_update_standard_value(self):
        """Modify a pre-existing standard parameter value and ensure stored"""

        # Get default value, as per setup
        default_val = params['update_files']

        # Change value to non-default
        params['update_files'] = not params['update_files']

        # Ensure it is in memory
        assert params['update_files'] is not default_val

        # Get a new parameters instance and verify information is retained
        new_params = eval(params.__repr__())
        assert new_params['update_files'] == params['update_files']

    def test_no_update_user_modules(self):
        """Ensure user_modules not modifiable via params"""

        # Attempt to change value
        with pytest.raises(ValueError) as err:
            params['user_modules'] = {}
        assert str(err).find('The pysat.utils.registry ') >= 0

    def test_add_user_parameter(self):
        """Add custom parameter and ensure present"""

        params['hi_there'] = 'hello there!'
        assert params['hi_there'] == 'hello there!'

        # Get a new parameters instance and verify information is retained
        new_params = eval(params.__repr__())
        assert new_params['hi_there'] == params['hi_there']

    def test_clear_and_restart(self):
        """Verify clear_and_restart method"""

        params.clear_and_restart()

        # check default value
        assert params['user_modules'] == {}

        # check value without working default
        assert params['data_dirs'] == []

        return


class TestCIonly(TravisCICleanSetup):
    """Tests where we mess with local settings.
    These only run in CI environments such as Travis and Appveyor to avoid
    breaking an end user's setup
    """

    # Set setup/teardown to the class defaults
    setup = TravisCICleanSetup.setup
    teardown = TravisCICleanSetup.teardown

    def test_initial_pysat_parameters_load(self, capsys):
        """Ensure initial parameters load routines work"""

        reload(pysat)

        captured = capsys.readouterr()
        # Ensure pysat is running in 'first-time' mode
        assert captured.out.find("Hi there!") >= 0

        # Remove pysat settings file
        shutil.move(os.path.join(self.root, 'pysat_settings.json'),
                    os.path.join(self.root, 'pysat_settings_moved.json'))

        # Ensure we can't create a parameters file without valid .json
        with pytest.raises(RuntimeError) as err:
            Parameters()
        assert str(err).find('pysat is unable to locate a user settings') >= 0

        # Move pysat settings file to cwd and try again
        shutil.move(os.path.join(self.root, 'pysat_settings_moved.json'),
                    os.path.join('./', 'pysat_settings.json'))

        Parameters()

        # Move pysat settings file back to original
        shutil.move(os.path.join('./', 'pysat_settings.json'),
                    os.path.join(self.root, 'pysat_settings.json'))

        # Make sure settings file created
        assert os.path.isfile(os.path.join(self.root, 'pysat_settings.json'))
        assert os.path.isdir(os.path.join(self.root, 'instruments'))
        assert os.path.isdir(os.path.join(self.root, 'instruments', 'archive'))
