from django.contrib import sitemaps
from django.urls import reverse


class StaticViewsSitemap(sitemaps.Sitemap):

    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return [
            'home',
            'terms_of_service',
            'cookies_policy',
        ]

    def location(self, item):
        return reverse(item)
