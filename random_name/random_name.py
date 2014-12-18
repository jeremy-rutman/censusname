from pkg_resources import resource_stream
import random
import csv
from . import formatters

# Name files should have at least the following columns:
# name (string)
# cumul_frequency (float) number from 0 to 100

SURNAME2000 = resource_stream('random_name', "data/dist.all.last.2000.csv")
SURNAME1990 = resource_stream('random_name', "data/dist.all.last.1990.csv")
MALEFIRST1990 = resource_stream('random_name', "data/dist.male.first.1990.csv")
FEMALEFIRST1990 = resource_stream('random_name', "data/dist.female.first.1990.csv")

# Name files don't contain every name, so hard coding the maximum frequency here.
# This way we don't over-pick the least common names
MAX_FREQUENCIES = {
    SURNAME2000: 89.75356,
    SURNAME1990: 90.483,
    MALEFIRST1990: 90.040,
    FEMALEFIRST1990: 90.024
}

GIVENNAMEFILES = {
    'male': MALEFIRST1990,
    'female': FEMALEFIRST1990
}

# 1990 is commented out because it's (a) out of date (b) not based on a random sample anyway
# Feel free to use it by doing something like:
# import random_names
# my_surnamefiles = { '1990': random_names.SURNAME1990 }
SURNAMEFILES = {
    '2000': SURNAME2000,
    # '1990': SURNAME1990
}

NAMEFILES = {
    'given': GIVENNAMEFILES,
    'surname': SURNAMEFILES
}

FORMATTERS = {
    'surname': [formatters.recapitalize_surnames]
}


class random_name(object):

    """Generate a random name from an arbitrary set of files"""

    def __init__(self, nameformat='{given} {surname}', namefiles=None, max_frequencies=None, **kwargs):
        self.namefiles = namefiles or NAMEFILES

        if self.namefiles == NAMEFILES:
            self.max_frequencies = MAX_FREQUENCIES

        # If no max frequencies given, assume they go to 100 for each file
        if max_frequencies is None:
            max_frequencies = dict((self.namefiles[k][x], 100) for k in self.namefiles.keys() for x in self.namefiles[k])

        self.nameformat = nameformat

        if 'csv_args' in kwargs:
            self.csv_args = kwargs['csv_args']
        else:
            self.csv_args = {'delimiter': ','}

        if 'formatters' in kwargs:
            if type(kwargs['formatters']) is not dict:
                raise TypeError("Keyword argument 'formatters' for random_name() must be a dict.")

            self.formatters = kwargs['formatters']
        else:
            self.formatters = FORMATTERS

        if 'capitalize' in kwargs:
            self.capitalize = kwargs['capitalize']
        else:
            self.capitalize = True

    def generate(self, nameformat=None, capitalize=None, formatters={}, **kwargs):
        '''Pick a random name form a specified list of name parts'''
        if nameformat is None:
            nameformat = self.nameformat

        if capitalize is None:
            capitalize = self.capitalize

        lines = self._get_lines(kwargs)
        names = dict((k, v['name']) for k, v in lines.items())

        if capitalize:
            names = dict((k, n.capitalize()) for k, n in names.items())

        merged_formatters = dict()

        try:
            merged_formatters = dict(
                (k, self.formatters.get(k, []) + formatters.get(k, [])) for k in set(self.formatters.keys() + formatters.keys())
            )
        except AttributeError:
            raise TypeError("keyword argument 'formatters' for random_name.generate() must be a dict")

        if merged_formatters:
            for key, functions in merged_formatters.items():
                # 'surname', [func_a, func_b]
                for func in functions:
                    # names['surname'] = func_a(name['surname'])
                    names[key] = func(names[key])

        return nameformat.format(**names)

    def _get_lines(self, nametypes):
        datafile, frequency, lines = '', 0.0, {}

        # The key of each name file is its namepart, e.g. surname or given
        for namepart in self.namefiles.keys():
            datafile = self._pick_file(namepart, nametypes.get(namepart, None))
            frequency = random.uniform(0, self.max_frequencies[datafile])
            lines[namepart] = self.pick_frequency_line(datafile, frequency)

        return lines

    def _pick_file(self, namepart, namekeys=None):
        result = None

        if type(namekeys) is not list:
            namekeys = [namekeys]

        if namekeys:
            key = random.choice(namekeys)
            result = self.namefiles[namepart].get(key)

        if result is None:
            return random.choice(self.namefiles[namepart].values())
        else:
            return result

    def pick_frequency_line(self, datastream, frequency, cumulativefield='cumulative_frequency'):
        '''Given a frequency, pick a line from a csv with a cumulative frequency field'''

        datastream.seek(0)
        reader = csv.DictReader(datastream, **self.csv_args)

        for line in reader:
            if float(line[cumulativefield]) >= frequency:
                return line


def main():
    # In the absence of tests, as least make sure specifying arguments doesn't break anything:
    rn = random_name('{given} {surname}', NAMEFILES, MAX_FREQUENCIES, csv_args={'delimiter': ','})
    print rn.generate()

if __name__ == '__main__':
    main()
