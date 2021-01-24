from urllib.request import Request, urlopen
import re
class BaseSub:
    groups = {}
    headers = {"USER-AGENT" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"}
    def __init__(self, url, include_keywords=[], exclude_keywords=[], mapping={}, misc="Misc", headers=None, should_include=None):
        #misc：所有其他不在mapping的节点
        mapping[""] = misc
        self.url = url
        self.include = include_keywords
        self.exclude = exclude_keywords
        self.mapping = mapping
        self.misc = misc
        if isinstance(headers, dict):
            self.headers = headers
        if should_include:
            self.__should_include = should_include

        #init dict
        for keyword, group_name in mapping.items():
            if group_name not in BaseSub.groups:
                BaseSub.groups[group_name] = []

        self.compile_proxies()

    def compile_proxies(self):
        print(f"Updating proxy list from {self.url}")
        try:
            self.__http_get_proxies()
        except ValueError:
            self.__proxies_from_file()

    def __should_include(self, string):
        string = string.lower()
        if "direct" in string:
            return False
        for keyword in self.exclude:
            if keyword in string:
                return False
        for keyword in self.include:
            if keyword in string:
                return True
        return len(self.include) == 0 and len(string) > 0

    def __http_get_proxies(self):
        req = Request(self.url)
        if self.headers:
            req.headers = self.headers
        content = urlopen(req).read().decode()
        lines = content.split("\n")
        captureProxies = False
        for line in lines:
            line = line.strip()
            if "沪港" in line:
                pass
            if captureProxies and ("[proxy" in line.lower() or "[rule" in line.lower()):
                break
            if captureProxies and self.__should_include(line):
                BaseSub.groups[self.__sort_proxy(line)].append(line)
            if not captureProxies and "[Proxy]" in line:
                captureProxies = True

    def __proxies_from_file(self):
        file = open(self.url, "r")
        for line in file.readlines():
            line = line.strip()
            if self.__should_include(line):
                BaseSub.groups[self.__sort_proxy(line)].append(line)

    def __sort_proxy(self, line):
        for k, v in self.mapping.items():
            if isinstance(k, str) and k in line:
                return v
            elif isinstance(k, frozenset):
                for x in k:
                    if x in line:
                        return v
        return self.mapping[""]

    @classmethod
    def append_to_subscription(cls, sub_path: str, default_groups = []):
        proxy_list = []
        for k, v in cls.groups.items():
            proxy_list += [str(proxy + "\n") for proxy in v]
        proxies = ''.join(proxy_list)
        file_read = open(sub_path, "r")
        content = file_read.read()
        portions = re.split("\[Proxy\]|\[Proxy Group\]|\[Rule\]", content)
        proxy_groups = []
        cur_groups = portions[2].split("\n")
        for group in cur_groups:
            for name in default_groups:
                if name == cls.get_name(group).strip():
                    proxy_groups.append(group)
                    proxy_groups.append("\n")

        for name, group_proxies in BaseSub.groups.items():
            li = []
            li.append(f"{name} = select, DIRECT, ")
            li += [cls.get_name(str(proxy)) + ", " for proxy in group_proxies]
            li.append("\n")
            proxy_groups.append(f"".join(li))
        proxy_content = ''.join(proxy_groups)
        content = f"{portions[0]}[Proxy]\n{proxies}\n\n[Proxy Group]\n{proxy_content}\n[Rule]{portions[3]}"
        file_write = open(sub_path, "w")
        file_write.write(content)
        print("Finished updating proxy list")

    @classmethod
    def get_name(cls, line: str):
        try:
            return line[:line.index("=")]
        except ValueError:
            return ""

import json
from os import getcwd

subs = json.load(open(f"{getcwd()}/config.json"))
myss = BaseSub(f"{getcwd()}/myss.list", mapping={"Germany" : "Europe", "Korea" : "Korea"})
nexitally = BaseSub(subs["nexitally"], mapping={"Taiwan": "Taiwan", "Hong Kong": "Hong Kong", "USA": "America", "Japan": "Japan", "Singapore": "Singapore", "Korea": "Korea", frozenset({"Germany", "France", "Netherlands", "United Kingdom", "Norway", "Sweden", "Bulgaria", "Austria", "Ireland", "Italy", "Hungary"}) : "Europe"})
amy = BaseSub(subs["amy"], mapping={"台湾": "Taiwan", "香港": "Hong Kong", "美国": "America", "日本": "Japan", "新加坡": "Singapore", "韩国": "Korea"})
fries = BaseSub(subs["fries"], include_keywords=["magic", "回国", "iplc", "iepl"], mapping={"回国" : "China", "台湾": "Taiwan", frozenset({"沪港", "香港"}): "Hong Kong", "美国": "America", "日本": "Japan", "新加坡": "Singapore", "韩国": "Korea"})

BaseSub.append_to_subscription(f"{getcwd()}/ShadowSocks.conf", default_groups=["ShadowSocks", "Netflix", "Speedtest", "Steam", "Plex"])
