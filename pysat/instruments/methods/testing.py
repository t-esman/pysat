import datetime as dt
import functools
import numpy as np
import os
import warnings

import pandas as pds

from pysat.utils import NetworkLock
from pysat import here

import pysat
logger = pysat.logger

ackn_str = ' '.join(("Test instruments provided through the pysat project.",
                     "https://www.github.com/pysat/pysat"))

# Load up citation information
with NetworkLock(os.path.join(here, 'citation.txt'), 'r') as locked_file:
    refs = locked_file.read()


def init(self, file_date_range=None, mangle_file_dates=False,
         test_init_kwrd=None):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    Shifts time index of files by 5-minutes if mangle_file_dates
    set to True at pysat.Instrument instantiation.

    Creates a file list for a given range if the file_date_range
    keyword is set at instantiation.

    Parameters
    ----------
    self : pysat.Instrument
        This object
    file_date_range : pds.date_range or NoneType
        Range of dates for files or None, if this optional argument is not
        used.
        (default=None)
    mangle_file_dates : bool
        If True, the loaded file list time index is shifted by 5-minutes.
    test_init_kwrd : any or NoneType
        Testing keyword (default=None)

    """

    logger.info(ackn_str)
    self.acknowledgements = ackn_str
    self.references = refs

    # Support file modification kwarg options
    modify_file_list_support(self, file_date_range=file_date_range,
                             mangle_file_dates=mangle_file_dates)

    # Assign parameters for testing purposes
    self.new_thing = True
    self.test_init_kwrd = test_init_kwrd

    return


def clean(self, test_clean_kwrd=None):
    """Cleaning function

    Parameters
    ----------
    self : pysat.Instrument
        This object
    test_clean_kwrd : any or NoneType
        Testing keyword (default=None)

    """

    self.test_clean_kwrd = test_clean_kwrd

    return


# Optional method
def preprocess(self, test_preprocess_kwrd=None):
    """Customization method that performs standard preprocessing.

    This routine is automatically applied to the Instrument object
    on every load by the pysat nanokernel (first in queue). Object
    modified in place.

    Parameters
    ----------
    self : pysat.Instrument
        This object
    test_preprocess_kwrd : any or NoneType
        Testing keyword (default=None)

    """

    self.test_preprocess_kwrd = test_preprocess_kwrd

    return


def list_files(tag=None, inst_id=None, data_path=None, format_str=None,
               file_date_range=None, test_dates=None,
               test_list_files_kwrd=None):
    """Produce a fake list of files spanning three years

    Parameters
    ----------
    tag : str
        pysat instrument tag (default=None)
    inst_id : str
        pysat satellite ID tag (default=None)
    data_path : str
        pysat data path (default=None)
    format_str : str
        file format string (default=None)
    file_date_range : pds.date_range
        File date range. The default mode generates a list of 3 years of daily
        files (1 year back, 2 years forward) based on the test_dates passed
        through below.  Otherwise, accepts a range of files specified by the
        user.
        (default=None)
    test_dates : dt.datetime
        Pass the _test_date object through from the test instrument files
    test_list_files_kwrd : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    Series of filenames indexed by file time

    """

    # Support keyword testing
    logger.info(''.join(('test_list_files_kwrd = ',
                         str(test_list_files_kwrd))))

    if data_path is None:
        data_path = ''

    # Determine the appropriate date range for the fake files
    if file_date_range is None:
        start = test_dates[''][''] - pds.DateOffset(years=1)
        stop = (test_dates[''][''] + pds.DateOffset(years=2)
                - pds.DateOffset(days=1))
        file_date_range = pds.date_range(start, stop)

    index = file_date_range

    # Create the list of fake filenames
    names = [data_path + date.strftime('%Y-%m-%d') + '.nofile'
             for date in index]

    return pds.Series(names, index=index)


def list_remote_files(tag=None, inst_id=None, data_path=None, format_str=None,
                      start=None, stop=None, test_dates=None, user=None,
                      password=None, test_list_remote_kwrd=None):
    """Produce a fake list of files spanning three years and one month to
    simulate new data files on a remote server

    Parameters
    ----------
    tag : str
        pysat instrument tag (default=None)
    inst_id : str
        pysat satellite ID tag (default=None)
    data_path : str
        pysat data path (default=None)
    format_str : str
        file format string (default=None)
    start : dt.datetime or NoneType
        Starting time for file list. A None value will start 1 year before
        test_date
        (default=None)
    stop : dt.datetime or NoneType
        Ending time for the file list.  A None value will stop 2 years 1 month
        after test_date
        (default=None)
    test_dates : dt.datetime
        Pass the _test_date object through from the test instrument files
    user : string
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied. (default=None)
    password : string
        Password for data download. (default=None)
    test_list_remote_kwrd : any or NoneType
        Testing keyword (default=None)

    Returns
    -------
    pds.Series
        Filenames indexed by file time, see list_files for more info

    """

    # Support keyword testing
    logger.info(''.join(('test_list_remote_kwrd = ',
                         str(test_list_remote_kwrd))))

    # Determine the appropriate date range for the fake files
    if start is None:
        start = test_dates[''][''] - pds.DateOffset(years=1)

    if stop is None:
        stop = (test_dates[''][''] + pds.DateOffset(years=2)
                - pds.DateOffset(days=1) + pds.DateOffset(months=1))

    file_date_range = pds.date_range(start, stop)

    return list_files(tag=tag, inst_id=inst_id, data_path=data_path,
                      format_str=format_str, file_date_range=file_date_range,
                      test_dates=test_dates)


def download(date_array, tag, inst_id, data_path=None, user=None,
             password=None, test_download_kwrd=None):
    """Simple pass function for pysat compatibility for test instruments.

    This routine is invoked by pysat and is not intended for direct use by the
    end user.

    Parameters
    ----------
    date_array : array-like
        list of datetimes to download data for. The sequence of dates need not
        be contiguous.
    tag : string
        Tag identifier used for particular dataset. This input is provided by
        pysat. (default='')
    inst_id : string
        Instrument ID string identifier used for particular dataset. This input
        is provided by pysat. (default='')
    data_path : string
        Path to directory to download data to. (default=None)
    user : string
        User string input used for download. Provided by user and passed via
        pysat. If an account is required for dowloads this routine here must
        error if user not supplied. (default=None)
    password : string
        Password for data download. (default=None)
    test_download_kwrd : any or NoneType
        Testing keyword (default=None)

    Raises
    ------
    ValueError
        When user/password are required but not supplied

    Warnings
    --------
    When no download support will be provided

    """

    # Support keyword testing
    logger.info(''.join(('test_download_kwrd = ', str(test_download_kwrd))))

    if tag == 'no_download':
        warnings.warn('This simulates an instrument without download support')

    # Check that user name and password are passed through the unit tests
    if tag == 'user_password':
        if (not user) and (not password):
            # Note that this line will be uncovered if test succeeds
            raise ValueError(' '.join(('Tests are not passing user and',
                                       'password to test instruments')))

    return


def generate_fake_data(t0, num_array, period=5820, data_range=[0.0, 24.0],
                       cyclic=True):
    """Generates fake data over a given range

    Parameters
    ----------
    t0 : float
        Start time in seconds
    num_array : array_like
        Array of time steps from t0.  This is the index of the fake data
    period : int
        The number of seconds per period.
        (default = 5820)
    data_range : float
        For cyclic functions, the range of data values cycled over one period.
        Not used for non-cyclic functions.
        (default = 24.0)
    cyclic : bool
        If True, assume that fake data is a cyclic function (ie, longitude,
        slt) that will reset to data_range[0] once it reaches data_range[1].
        If False, continue to monotonically increase

    Returns
    -------
    data : array-like
        Array with fake data

    """

    if cyclic:
        uts_root = np.mod(t0, period)
        data = (np.mod(uts_root + num_array, period)
                * (np.diff(data_range)[0] / float(period))) + data_range[0]
    else:
        data = ((t0 + num_array) / period).astype(int)

    return data


def generate_times(fnames, num, freq='1S'):
    """Construct list of times for simulated instruments

    Parameters
    ----------
    fnames : list
        List of filenames.
    num : int
        Number of times to generate
    freq : string
        Frequency of temporal output, compatible with pandas.date_range
        [default : '1S']

    Returns
    -------
    uts : array
        Array of integers representing uts for a given day
    index : DatetimeIndex
        The DatetimeIndex to be used in the pysat test instrument objects
    date : datetime
        The requested date reconstructed from the fake file name

    """

    if isinstance(num, str):
        estr = ''.join(('generate_times support for input strings interpreted ',
                        'as the number of times has been deprecated. Please ',
                        'switch to using integers.'))
        warnings.warn(estr, DeprecationWarning)

    uts = []
    indices = []
    dates = []
    for loop, fname in enumerate(fnames):
        # Grab date from filename
        parts = os.path.split(fname)[-1].split('-')
        yr = int(parts[0])
        month = int(parts[1])
        day = int(parts[2][0:2])
        date = dt.datetime(yr, month, day)
        dates.append(date)

        # Create one day of data at desired frequency
        end_date = date + dt.timedelta(seconds=86399)
        index = pds.date_range(start=date, end=end_date, freq=freq)
        index = index[0:num]
        indices.extend(index)
        uts.extend(index.hour * 3600 + index.minute * 60 + index.second
                   + 86400. * loop)

    # Combine index times together
    index = pds.DatetimeIndex(indices)

    # Make UTS an array
    uts = np.array(uts)

    return uts, index, dates


def define_period():
    """Define the default periods for the fake data functions

    Returns
    -------
    def_period : dict
        Dictionary of periods to use in test instruments

    Note
    ----
    Local time and longitude slightly out of sync to simulate motion of Earth

    """

    def_period = {'lt': 5820,  # 97 minutes
                  'lon': 6240,  # 104 minutes
                  'angle': 5820}

    return def_period


def define_range():
    """Define the default ranges for the fake data functions

    Returns
    -------
    def_range : dict
        Dictionary of periods to use in test instruments

    """

    def_range = {'lt': [0.0, 24.0],
                 'lon': [0.0, 360.0],
                 'angle': [0.0, 2.0 * np.pi]}

    return def_range


def modify_file_list_support(self, file_date_range=None,
                             mangle_file_dates=None):
    """Support modifying file lists for testing Instruments for unit tests.

    Parameters
    ----------
    self : pysat.Instrument
        This object

    """

    # Work on file index if keyword present
    if file_date_range:
        # Set list files routine to desired date range and
        # attach to the Instrument object.
        fdr = file_date_range
        self._list_files_rtn = functools.partial(list_files,
                                                 file_date_range=fdr)
        # Update files version as well
        self.files.list_files_rtn = functools.partial(list_files,
                                                      file_date_range=fdr)
        self.files.refresh()

    # Mess with file dates if kwarg option present
    if mangle_file_dates:
        self.files.files.index = \
            self.files.files.index + dt.timedelta(minutes=5)

    return
