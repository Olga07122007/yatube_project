from django.views.decorators.cache import cache_page


FIRST_CHARACTERS_OF_POST = 15
QUANTITY_OF_POSTS = 10
CACHE_PAGE = cache_page(20, key_prefix='index_page')
