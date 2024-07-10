from django.contrib.sitemaps import Sitemap
from .models import Post


class PostSitemap(Sitemap):
    '''
    Карта сайта для постов в блоге
    '''
    changefreq = 'weekly'   #   Частота изменения страниц и их релевантность на веб-сайте (максимальное значение равно 1)
    priority = 0.9

    def items(self):
        return Post.published.all()

    def lastmod(self, obj):
        return obj.updated