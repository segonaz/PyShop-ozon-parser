if __name__ == "__main__":
    import os

    from scrapy.cmdline import execute

    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    SPIDER_NAME = "ozon_smartphones"
    try:
        execute(
            [
                "scrapy",
                "crawl",
                SPIDER_NAME,
                "-s",
                "FEED_EXPORT_ENCODING=utf-8",
            ]
        )
    except SystemExit:
        pass
