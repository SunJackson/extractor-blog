#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @author:SunJackson
# @datetime:2020/11/23 10:50
# @file: utils.py
import re
from urllib.parse import urljoin, urlparse, urlunparse
from posixpath import normpath

def urlJoin(base, url):
    '''
    url 拼接
    url = 'http://karpathy.github.io/2014/07/03/feature-learning-escapades/'

    url_join(url, '../assets/nips2012.jpeg')
    'http://karpathy.github.io/2014/07/03/assets/nips2012.jpeg'

    url_join(url, './assets/nips2012.jpeg')
    'http://karpathy.github.io/2014/07/03/feature-learning-escapades/assets/nips2012.jpeg'

    url_join(url, '/assets/nips2012.jpeg')
    'http://karpathy.github.io/assets/nips2012.jpeg'

    url_join(url,'http://karpathy.github.io/assets/nips2012.jpeg')
    'http://karpathy.github.io/assets/nips2012.jpeg'
    '''
    if not url.startswith('.') and not url.startswith('/'):
        return url
    url1 = urljoin(base, url)
    arr = urlparse(url1)
    path = normpath(arr[2])
    return urlunparse((arr.scheme, arr.netloc, path, arr.params, arr.query, arr.fragment))
def replaceCharEntity(html_str):
    """
    去除掉无用字符串
    :param htmlstr:
    :return:
    """
    CHAR_ENTITIES = {'nbsp': ' ',
                     '160': ' ',
                     'lt': '<',
                     '60': '<',
                     'gt': '>',
                     '62': '>',
                     'amp': '&',
                     '38': '&',
                     'quot': '"',
                     '34': '"', }
    re_charEntity = re.compile(r'&#?(?P<name>\w+);')
    sz = re_charEntity.search(html_str)
    while sz:
        key = sz.group('name')
        try:
            html_str = re_charEntity.sub(CHAR_ENTITIES[key], html_str, 1)
            sz = re_charEntity.search(html_str)
        except KeyError:
            # 以空串代替
            html_str = re_charEntity.sub('', html_str, 1)
            sz = re_charEntity.search(html_str)
    return html_str


def filterTags(html_str):
    """
    去除html文本中的标签
    :param html_str:
    :return:
    """
    re_doctype = re.compile(r'<!DOCTYPE.*?>', re.DOTALL)
    re_nav = re.compile(r'<nav.+</nav>', re.DOTALL)
    re_cdata = re.compile(r'//<!\[CDATA\[.*//\]\]>', re.DOTALL)
    re_script = re.compile(
        r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', re.DOTALL | re.I)
    re_style = re.compile(
        r'<\s*style[^>]*>.*?<\s*/\s*style\s*>', re.DOTALL | re.I)
    re_textarea = re.compile(
        r'<\s*textarea[^>]*>.*?<\s*/\s*textarea\s*>', re.DOTALL | re.I)
    re_br = re.compile(r'<br\s*?/?>')
    re_h = re.compile(r'</?\w+.*?>', re.DOTALL)
    re_comment = re.compile(r'<!--.*?-->', re.DOTALL)
    re_space = re.compile(r' +')
    s = re_cdata.sub('', html_str)
    s = re_doctype.sub('', s)
    s = re_nav.sub('', s)
    s = re_script.sub('', s)
    s = re_style.sub('', s)
    s = re_textarea.sub('', s)
    s = re_br.sub('', s)
    s = re_h.sub('', s)
    s = re_comment.sub('', s)
    s = re.sub('\\t', '', s)
    s = re_space.sub(' ', s)
    s = replaceCharEntity(s)
    return s


def getNetloc(url):
    """
    获取netloc
    :param url:
    :return:  netloc
    """
    netloc = urlparse(url).netloc
    return netloc or None