from datetime import datetime, timedelta
import pandas as pd

from footballdata.common import (
    datadir,
    download_and_save,
    TEAMNAME_REPLACEMENTS)

import sys
if sys.version_info >= (3, 4):
    from pathlib import Path
else:
    from pathlib2 import Path


class ClubElo(object):
    """Provides pandas.DataFrames from CSV API at http://api.clubelo.com

    Data will be downloaded as necessary and cached locally in ./data

    """

    # This class holds no state. We use a class anyway to maintain consistency
    # with the rest of the package

    def by_date(self, date=None):
        """Returns ELO scores for all teams at specified date in
        a pandas.DataFrame.

        If no date is specified, get today's scores

        Parameters
        ----------
        date : datetime object or string like 'YYYY-MM-DD'
        """

        if not date:
            date = datetime.today()
        elif isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        else:
            pass  # Assume datetime object

        datestring = date.strftime("%Y-%m-%d")
        filepath = Path(datadir(), 'clubelo_{}.csv'.format(datestring))
        url = 'http://api.clubelo.com/{}'.format(datestring)

        if not filepath.exists():
            download_and_save(url, filepath)

        df = (pd.read_csv(str(filepath),
                          parse_dates=['From', 'To'],
                          infer_datetime_format=True,
                          dayfirst=False
                          )
              .rename(columns={'Club': 'Team'})
              )

        df.replace(
            {'Team': TEAMNAME_REPLACEMENTS},
            inplace=True
        )
        df = df.reset_index().set_index('Team')
        return df

    def team_history(self, team, max_age=1):
        """Downloads full ELO history for one team

        Returns pandas.DataFrame

        Parameters
        ----------
        club : string club name
        max_age : max. age of local file before re-download
                integer for age in days, or timedelta object
        """

        filepath = Path(datadir(), 'clubelo_{}.csv'.format(team))
        url = 'http://api.clubelo.com/{}'.format(team)

        if isinstance(max_age, int):
            _max_age = timedelta(days=max_age)
        elif isinstance(max_age, timedelta):
            _max_age = max_age
        else:
            raise TypeError('max_age must be of type int or datetime.timedelta')  # nopep8

        if not filepath.exists():
            download_and_save(url, filepath)
        else:
            last_modified = datetime.fromtimestamp(filepath.stat().st_mtime)
            now = datetime.now()
            if (now - last_modified) > _max_age:
                download_and_save(url, filepath)

        df = (pd.read_csv(str(filepath),
                          parse_dates=['From', 'To'],
                          infer_datetime_format=True,
                          dayfirst=False)
              .rename(columns={'Club': 'Team'})
              .set_index('From')
              .sort_index()
              )
        if len(df) > 0:
            return df
        else:
            # clubelo.com returns a CSV with just a header for nonexistent club
            raise ValueError('No data found for club {}'.format(team))
