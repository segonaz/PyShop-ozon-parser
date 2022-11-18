from time import time

import pandas as pd

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class OzonPipeline:
    def process_item(self, item, spider):
        self.clean_os_version(item)
        self.data.append(item)

        return item

    def clean_os_version(self, item):
        if item["os_version"]:
            start_position = item["os_version"].find(" ")
            item["os_version"] = item["os_version"][start_position + 1 :]
            return item

    def open_spider(self, spider):
        self.data = []

    def close_spider(self, spider):
        df = pd.DataFrame(self.data)
        grouped = df.groupby("os_name", as_index=False)["os_version"].value_counts(dropna=False)
        grouped = grouped.sort_values(by=["count"], ascending=False)
        grouped.insert(2, "split", "-")
        df_text = grouped.to_string(header=False, index=False)
        file_name = f"./output/{spider.name}_{int(time() * 1000)}.txt"
        with open(file_name, "w") as f:
            f.write(df_text)
