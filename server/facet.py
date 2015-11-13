# -*- coding: utf-8 -*-
"""A class that encapsulates facet search."""
import json

PREFIX_MAGNITITUDE = {
    "P": 1000000000000000,
    "T": 1000000000000,
    "G": 1000000000,
    "M": 1000000,
    "k": 1000,
    "h": 100,
    "c": 0.01,
    "m": 0.001,
    "μ": 0.000001,
    "n": 0.000000001,
    "p": 0.000000000001
}

class Facet(object):
    """A class that encapsulates facet search."""

    def __init__(self, path):
        self.unit2prop = {}
        self.conversion = {}
        info = json.load(open(path), encoding='utf-8')
        for prop in info:
            prop_name = info[prop]["name"]
            unitlist = info[prop]['units']
            for unit in unitlist:
                unit_name = unit['name']
                self.unit2prop[unit_name] = (prop, prop_name)
                tobase = unit['in-base-unit']
                if len(tobase) == 2:
                    self.conversion[unit_name] = unit['in-base-unit']

    def normalize(self, value, unit, prefix):
        #print unit
        multiplier = self.conversion[unit]['multiplier']
        offset = self.conversion[unit]['zero-point']
        normalized = value * multiplier + offset
        if prefix:
            normalized *= PREFIX_MAGNITITUDE[prefix]
        return normalized

    def get_filter_index(self, hits):
        retlist = []
        propset = set()
        for hit in hits:
            celllist = []
            data = hit['data_rows']
            for row in data:
                for cell in row:
                    #print cell
                    value = {}
                    if cell['type'] != -1 and cell['unit']:
                        if 'prefix' in cell and 'unit' in cell and 'mainValue' in cell:
                            value['value'] = self.normalize(cell['mainValue'], cell['unit'], cell['prefix'])
                            value['id'] = cell['cellid']
                            prop_id, prop_name = self.unit2prop[cell['unit']]
                            value['prop'] = prop_id
                            celllist.append(value)
                            propset.add((prop_id, prop_name))
            retlist.append(dict(date=hit['date'], cell_list=celllist))
        return retlist, [dict(id=p[0], name=p[1]) for p in propset]
