from typing import List, Union, Dict
from math import ceil

from common.providers import s3Provider, awsKeyProvider

import logging

class DataClass():

    page_size = None
    page_number = None

    def __init__(self):
        self.page_size = 50
        self.page_number = 1


    def paginate(self, to_paginate:List, page_number:int=1, page_size:int=10) -> Union[List,Dict]:
        """
        This function paginates arrays, so that large data queries can be minimised where possible

        Args:


        Returns:

        """ 
        if page_size is None:
            page_size = self.page_size
        if page_number is None:
            page_number = self.page_number
        _pagination = {
            'current_page': page_number,
            'page_size': page_size,
            'page_count':0,
            'start':0,
            'end':0,
            'total':0,
            'pages':[]
        }
        if len(to_paginate) == 0:
            return [], _pagination
        else:
            _start = ((page_number - 1 ) * page_size) + 1
            _end = (page_number * page_size)
            _total = len(to_paginate)
            _page_count = ceil(_total/page_size)
            if page_number > _page_count:
                _pagination['current_page'] = _page_count
            if len(to_paginate) < _end:
                end = len(to_paginate)
            _pagination['start'] = _start
            _pagination['end'] = _end
            _pagination['total'] = _total
            _pagination['page_count'] = _page_count
            _pagination['pages'] = list(range(1,_page_count+1))
            _paginated = to_paginate[_start-1:_end]
            return _paginated, _pagination



class FacetClass():
    def __init__(self, _name, _facet, _aws_config):
        self._name = _name
        self._facet = _facet
        self._s3 = s3Provider(_aws_config)


    def get(self, facet, pdb_code):
        item_key = awsKeyProvider().block_key(pdb_code, facet, 'info')
        item, success, errors = self._s3.get(item_key)
        if success:
            return item
        else:
            return {}


    def hydrate(self, _itemset):
        itemset, success, errors = _itemset
        if itemset is not None:
            itemset['hydrated_members'] = [{'pdb_code':pdb_code, self._facet: self.get(self._facet, pdb_code)} for pdb_code in itemset['members']]
        return itemset, success, errors
