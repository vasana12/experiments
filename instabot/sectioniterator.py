from typing import Any,Dict, Iterator, Optional
import logging
from .instabotcontext import InstabotContext

logger = logging.getLogger(__name__)

# 로그의 출력 기준 설정
logger.setLevel(logging.DEBUG)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class SectionIterator(Iterator):
    """Iterator for the 'sections' responses."""
    def __init__(self,
                 context: InstabotContext,
                 sections_extractor,
                 media_wrapper,
                 query_path: str,
                 first_data: Optional[Dict[str, Any]] = None):
        self._context = context
        self._sections_extractor = sections_extractor
        self._media_wrapper = media_wrapper
        self._query_path = query_path
        self._data = first_data or self._query()
        self._page_index = 0
        self._section_index = 0
    def __iter__(self):
        return self

    def _query(self, max_id: Optional[str] = None) -> Dict[str, Any]:
        pagination_variables = {"max_id": max_id} if max_id is not None else {}
        return self._sections_extractor(
            self._context.get_json(self._query_path, params={"__a": 1, **pagination_variables})
        )

    def __next__(self):
        """
        when page index is smaller than section total number and section index < media of iteration,
        we have to add 1 to the section index

        when section index > media number
        we have to add 1 to the page index and make section index zero
        """
        if self._page_index < len(self._data['sections']):
            media = self._data['sections'][self._page_index]['layout_content']['medias'][self._section_index]['media']
            self._section_index += 1
            if self._section_index >= len(self._data['sections'][self._page_index]['layout_content']['medias']):
                self._section_index = 0
                self._page_index += 1
            return self._media_wrapper(media)
        if self._data['more_available']:
            self._page_index, self._section_index, self._data = 0, 0, self._query(self._data["next_max_id"])
            return self.__next__()
        raise StopIteration()
