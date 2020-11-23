# coding=utf-8

import requests
import re
import chardet
from extractorblog.readability import Readability
from extractorblog import tomd
from extractorblog.utils.utils import filterTags, urlJoin
from extractorblog.utils.textRank4Keywords import TextRank


def fixUrl(article_url, text):
    fix_map = {
        'src': 'src=[\'|\"](?P<url>.*?)[\'|\"]',
        'href': 'href=[\'|\"](?P<url>.*?)[\'|\"]',
    }
    for key, value in fix_map.items():
        def joinUrl(obj):
            return '{}="{}"'.format(key, urlJoin(article_url, obj.group('url')))
        _re = re.compile(value)
        text = _re.sub(joinUrl, text)
    return text


class ExtractorBlog:
    def __init__(self):
        self.body_html = None
        self.title = None
        self.html = None
        self.body_md = None
        self.body_text = None

    def filterHtml(self, html):
        filter_map = {
            'amp;': ''
        }
        for (key, value) in filter_map.items():
            html = html.replace(key, value)
        return html

    def get(self, url, params=None, **kwargs):
        response = requests.get(url, params=params, **kwargs)
        encode_info = chardet.detect(response.content)
        response.encoding = encode_info['encoding']
        response_text = response.text
        html_fix = fixUrl(url, response_text)
        html_filter = self.filterHtml(html_fix)
        readability = Readability(html_filter, url)
        self.title = readability.title
        self.body_html = readability.content
        self.html = html_fix
        self.body_text = filterTags(self.body_html)

    def toMarkdown(self):
        """
        生成markdown
        :return:
        """

        def fixMd(md):
            # 去除图片生成md时产生重复地址
            md_split = md.split('\n')
            fix_md_str = []
            for i in range(len(md_split)):
                if i < len(md_split) - 2 and md_split[i] == md_split[i + 2] and md_split[i] \
                        and '```' not in md_split[i]:
                    continue
                fix_md_str.append(md_split[i])
            return '\n'.join(fix_md_str)

        if self.body_html:
            md = tomd.Tomd(self.html).markdown
            self.body_md = fixMd(md)

    def getKeyWords(self, window=5, alpha=0.85, iternum=50, n=5):
        """
        获取文章关键词
        :param window: 窗口大小
        :param alpha:
        :param iternum: 迭代次数
        :param n: 返回关键词个数
        :return: keys
        """
        tr = TextRank(self.body_text, window, alpha, iternum)
        keys = tr.getTopKeyWords(n)
        return keys

    def getSummary(self):
        """
        自动获取摘要
        :return:
        """
        pass


if __name__ == '__main__':
    ET = ExtractorBlog()
    ua_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
    }
    html_content = ET.get('https://ramiro.org/notebook/reddit-best-post-times/', headers=ua_headers)
    ET.toMarkdown()
    print(ET.body_md)
