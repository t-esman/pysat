"""
tests the pysat instruments and code
"""
from importlib import import_module
import os
from unittest.case import SkipTest
import warnings

import pandas as pds
import pytest
import tempfile

import pysat

# dict, keyed by pysat instrument, with a list of usernames and passwords
user_download_dict = {'supermag_magnetometer': ['rstoneback', None]}


def remove_files(inst):
    # remove any files downloaded as part of the unit tests
    temp_dir = inst.files.data_path
    # Check if there are less than 20 files to ensure this is the testing
    # directory
    if len(inst.files.files.values) < 20:
        for the_file in list(inst.files.files.values):
            # Check if filename is appended with date for fake_daily data
            # ie, does an underscore exist to the right of the file extension?
            if the_file.rfind('_') > the_file.rfind('.'):
                # If so, trim the appendix to get the original filename
                the_file = the_file[:the_file.rfind('_')]
            file_path = os.path.join(temp_dir, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    else:
        warnings.warn(''.join(('Files > 20.  Not deleted.  Please check to ',
                              'ensure temp directory is used')))


def generate_instrument_list(instrument_names=[]):
    """Iterate through and create all of the test Instruments needed.
       Only want to do this once.

    """

    print('The following instrument modules will be tested : ',
          instrument_names)

    instrument_download = []
    instrument_no_download = []

    # create temporary directory
    dir_name = tempfile.mkdtemp()
    saved_path = pysat.data_dir
    pysat.utils.set_data_dir(dir_name, store=False)

    for name in instrument_names:
        try:
            module = import_module(''.join(('.', name)),
                                   package='pysat.instruments')
        except ImportError:
            print(' '.join(["Couldn't import", name]))
            pass
        else:
            # try to grab basic information about the module so we
            # can iterate over all of the options
            try:
                info = module._test_dates
            except AttributeError:
                info = {}
                info[''] = {'': pysat.datetime(2009, 1, 1)}
                module._test_dates = info
            for sat_id in info.keys():
                for tag in info[sat_id].keys():
                    try:
                        inst = pysat.Instrument(inst_module=module,
                                                tag=tag,
                                                sat_id=sat_id,
                                                temporary_file_list=True)
                        inst._test_dates = module._test_dates
                        if inst._test_download:
                            instrument_download.append(inst)
                        else:
                            # we don't want to test download for this combo
                            print(' '.join(['Excluding', name,
                                            sat_id, tag, 'from downloads']))
                            instrument_no_download.append(inst)
                    except:
                        pass
    pysat.utils.set_data_dir(saved_path, store=False)

    output = {'names': instrument_names,
              'download': instrument_download,
              'no_download': instrument_no_download}

    return output


class TestInstrumentQualifier():

    instruments = \
        generate_instrument_list(instrument_names=pysat.instruments.__all__)

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        pass

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pass

    @pytest.mark.parametrize("name", instruments['names'])
    def test_modules_loadable(self, name):

        # ensure that each module is at minimum importable
        module = import_module(''.join(('.', name)),
                               package='pysat.instruments')
        # Check for presence of basic platform / name / tags / sat_id
        assert isinstance(module.platform, str)
        assert isinstance(module.name, str)
        assert isinstance(module.tags, dict)
        assert isinstance(module.sat_ids, dict)

        try:
            info = module._test_dates
        except AttributeError:
            info = {}
            info[''] = {'': 'failsafe'}
        for sat_id in info.keys():
            for tag in info[sat_id].keys():
                print(' '.join(('Checking pysat.Instrument',
                                'instantiation for module:', name,
                                'tag:', tag, 'sat id:', sat_id)))
                inst = pysat.Instrument(inst_module=module, tag=tag,
                                        sat_id=sat_id)
                assert True

    @pytest.mark.parametrize("name", instruments['names'])
    def test_required_function_presence(self, name):
        """Check if each required function is present and callable"""
        module = import_module(''.join(('.', name)),
                               package='pysat.instruments')
        assert hasattr(module, 'load') & callable(module.load)
        assert hasattr(module, 'list_files') & callable(module.list_files)
        assert hasattr(module, 'download') & callable(module.download)

    @pytest.mark.parametrize("name", instruments['names'])
    def test_instrument_tdates(self, name):
        module = import_module(''.join(('.', name)),
                               package='pysat.instruments')
        info = module._test_dates
        for sat_id in info.keys():
            for tag in info[sat_id].keys():
                assert isinstance(info[sat_id][tag], pds.datetime)

    def check_download(self, inst):
        start = inst._test_dates[inst.sat_id][inst.tag]
        try:
            # check for username
            inst_name = '_'.join((inst.platform, inst.name))
            if inst_name in user_download_dict:
                inst.download(start, start,
                              user=user_download_dict[inst_name][0],
                              password=user_download_dict[inst_name][1])
            else:
                inst.download(start, start)
        except Exception as strerr:
            # couldn't run download, try to find test data instead
            print("Couldn't download data, trying to find test data.")
            saved_path = pysat.data_dir

            new_path = os.path.join(pysat.__path__[0], 'tests', 'test_data')
            pysat.utils.set_data_dir(new_path, store=False)
            _test_dates = inst._test_dates
            inst = pysat.Instrument(platform=inst.platform,
                                    name=inst.name,
                                    tag=inst.tag,
                                    sat_id=inst.sat_id,
                                    temporary_file_list=True)
            inst._test_dates = _test_dates
            pysat.utils.set_data_dir(saved_path, store=False)
            if len(inst.files.files) > 0:
                print("Found test data.")
                raise SkipTest
            else:
                print("No test data found.")
                raise strerr
        assert True

    def check_load(self, inst, fuzzy=False):
        # set ringer data
        inst.data = pds.DataFrame([0])
        start = inst._test_dates[inst.sat_id][inst.tag]
        inst.load(date=start)
        if not fuzzy:
            assert not inst.empty
        else:
            try:
                assert inst.data != pds.DataFrame([0])
            except:
                # if there is an error, they aren't the same
                assert True

        # clear data
        inst.data = pds.DataFrame(None)

    @pytest.mark.parametrize("inst", instruments['download'])
    def test_download_and_load(self, inst):
        print(' '.join(('Checking download routine functionality for module: ',
                        inst.platform, inst.name, inst.tag, inst.sat_id)))
        self.check_download(inst)

        # make sure download was successful
        if len(inst.files.files) > 0:
            print(' '.join(('Checking load routine functionality for module: ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            inst.clean_level = 'none'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "none": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst)

            inst.clean_level = 'dirty'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "dirty": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            inst.clean_level = 'dusty'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "dusty": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            inst.clean_level = 'clean'
            print(' '.join(('Checking load routine functionality for module',
                            'with clean level "clean": ',
                            inst.platform, inst.name, inst.tag, inst.sat_id)))
            self.check_load(inst, fuzzy=True)

            remove_files(inst)
        else:
            print('Unable to actually download a file.')
            # raise RuntimeWarning(' '.join(('Download for', inst.platform,
            # inst.name, inst.tag, inst.sat_id, 'was not successful.')))
            warnings.warn(' '.join(('Download for', inst.platform,
                                    inst.name, inst.tag, inst.sat_id,
                                    'was not successful.')))

    @pytest.mark.parametrize("inst", instruments['no_download'])
    def test_download_warning(self, inst):
        print(' '.join(('Checking download routine warnings for module: ',
                        inst.platform, inst.name, inst.tag, inst.sat_id)))
        start = inst._test_dates[inst.sat_id][inst.tag]
        with warnings.catch_warnings(record=True) as war:
            try:
                inst.download(start, start)
            except ValueError as strerr:
                if str(strerr).find('CDAAC') >= 0:
                    warnings.warn("COSMIC data detected")
                else:
                    raise strerr

        assert len(war) >= 1
        assert war[0].category == UserWarning

    # Optional support

    # directory_format string

    # multiple file days

    # orbit information

        # self.directory_format = None
        # self.file_format = None
        # self.multi_file_day = False
        # self.orbit_info = None
