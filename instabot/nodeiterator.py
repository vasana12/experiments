from datetime import datetime, timedelta
from typing import Dict, Iterator, Optional
from .exceptions import QueryReturnedBadRequestException
from .instabotcontext import InstabotContext



class NodeIterator(Iterator):
    _graphql_page_length = 50
    _shelf_life = timedelta(days=29)
    def __init__(self,
                 context: InstabotContext,
                 query_hash: str,
                 edge_extractor,
                 node_wrapper,
                 query_variables= None,
                 query_referer = None,
                 first_data = None):
        self.logger = context.logger
        self._context = context
        self._query_hash = query_hash
        self._edge_extractor = edge_extractor
        self._node_wrapper = node_wrapper
        self._query_variables = query_variables if query_variables is not None else {}
        self._query_referer = query_referer
        self._page_index = 0
        self._total_index = 0
        if first_data is not None:
            self._data = first_data
        else:
            self._data = self._query()
        self._first_node: Optional[Dict] = None

    def _query(self, after: Optional[str] = None) -> Dict:
        pagination_variables = {'first': NodeIterator._graphql_page_length}
        if after is not None:
            pagination_variables['after'] = after
        try:
            data = self._edge_extractor(
                self._context.graphql_query(
                    self._query_hash, {**self._query_variables, **pagination_variables}, self._query_referer
                )
            )
            self._best_before = datetime.now() + NodeIterator._shelf_life
            return data

        except QueryReturnedBadRequestException:
            new_page_length = int(NodeIterator._graphql_page_length / 2)
            if new_page_length >= 12:
                NodeIterator._graphql_page_length = new_page_length
                self._context.logger.error("HTTP Error 400 (Bad Request) on GraphQL Query. Retrying with shorter page length.")
                return self._query(after)
            else:
                raise

    def __iter__(self):
        return self

    def __next__(self):
        if self._page_index < len(self._data['edges']):
            node = self._data['edges'][self._page_index]['node']
            page_index, total_index = self._page_index, self._total_index
            try:
                self._page_index += 1
                self._total_index += 1
            except KeyboardInterrupt:
                self._page_index, self._total_index = page_index, total_index
                raise
            item = self._node_wrapper(node)
            if self._first_node is None:
                self._first_node = node
            return item
        if self._data['page_info']['has_next_page']:
            query_response = self._query(self._data['page_info']['end_cursor'])
            if self._data['edges'] != query_response['edges']:
                page_index, data = self._page_index, self._data
                try:
                    self._page_index = 0
                    self._data = query_response
                except KeyboardInterrupt:
                    self._page_index, self._data = page_index, data
                    raise
                return self.__next__()
        raise StopIteration()


