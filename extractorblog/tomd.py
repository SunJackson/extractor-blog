# coding: utf-8

import re
import os
import warnings
from .utils.utils import filterTags

MARKDOWN = {
    'h1': ('\n# ', '\n'),
    'h2': ('\n## ', '\n'),
    'h3': ('\n### ', '\n'),
    'h4': ('\n#### ', '\n'),
    'h5': ('\n##### ', '\n'),
    'h6': ('\n###### ', '\n'),
    'code': ('`', '`'),
    'ul': ('', ''),
    'ol': ('', ''),
    'li': ('- ', ''),
    'blockquote': ('\n> ', '\n'),
    'em': ('*', '*'),
    'strong': ('**', '**'),
    'block_code': ('\n```\n', '\n```\n'),
    'span': ('', ''),
    'p': ('\n', '\n\n'),
    'p_with_out_class': ('\n', '\n'),
    'inline_p': ('', ''),
    'inline_p_with_out_class': ('', ''),
    'b': ('**', '**'),
    'i': ('*', '*'),
    'del': ('~~', '~~'),
    'hr': ('\n---', '\n'),
    'thead': ('\n', ''),
    'tbody': ('\n', '\n'),
    'td': ('|', ''),
    'th': ('|', ''),
    'tr': ('', '\n'),
    'table': ('', '\n'),
    'e_p': ('', '\n'),
    'img': ('', '\n')
}

BlOCK_ELEMENTS = {
    'h1': '<h1.*?>(.*?)</h1>',
    'h2': '<h2.*?>(.*?)</h2>',
    'h3': '<h3.*?>(.*?)</h3>',
    'h4': '<h4.*?>(.*?)</h4>',
    'h5': '<h5.*?>(.*?)</h5>',
    'h6': '<h6.*?>(.*?)</h6>',
    'hr': '<hr/>',
    'blockquote': '<blockquote.*?>([\s\S].*?)</blockquote>',
    'ul': '<ul.*?>(.*?)</ul>',
    'ol': '<ol.*?>(.*?)</ol>',
    'block_code': '<pre.*?><code.*?>([\s\S].*?)</code></pre>',
    'p': '<p\s.*?>(.*?)</p>',
    'p_with_out_class': '<p>([\s\S].*?)</p>',
    'thead': '<thead.*?>([\s\S].*?)</thead>',
    'tr': '<tr.*?>([\s\S].*?)</tr>',
    'img': '(<img [\s\S].*?/>)',

}
'''
<pre><span>import</span> <span>pandas</span> <span>as</span> <span>pd</span> <span># This is the standard</span>
</pre>
'''
INLINE_ELEMENTS = {
    'td': '<td.*?>((.|\n)*?)</td>',  # td element may span lines
    'tr': '<tr.*?>((.|\n)*?)</tr>',
    'th': '<th.*?>(.*?)</th>',
    'b': '<b.*?>(.*?)</b>',
    'i': '<i.*?>(.*?)</i>',
    'del': '<del.*?>(.*?)</del>',
    'inline_p': '<p\s.*?>(.*?)</p>',
    'p': '<p\s.*?>(.*?)</p>',
    'inline_p_with_out_class': '<p>(.*?)</p>',
    'code': '<code.*?>(.*?)</code>',
    'span': '<span.*?>(.*?)</span>',
    'ul': '<ul.*?>(.*?)</ul>',
    'ol': '<ol.*?>(.*?)</ol>',
    'li': '<li.*?>(.*?)</li>',
    'img': '<img.*?src="(.*?)".*?>(.*?)</img>',
    'img_single': '<img.*?src="(.*?)".*?/>',
    'img_single_no_close': '<img.*?src="(.*?)".*?>',
    'a': '<a.*?href="(.*?)".*?>(.*?)</a>',
    'em': '<em.*?>(.*?)</em>',
    'strong': '<strong.*?>(\s*)(.*?)(\s*)</strong>',
    'tbody': '<tbody.*?>([\s\S].*?)</tbody>',
}

DELETE_ELEMENTS = ['<span.*?>', '</span>', '<div.*?>', '</div>', '<br clear="none"/>', '<center.*?>', '</center>']


class Element:
    def __init__(self, start_pos, end_pos, content, tag, folder, is_block=False):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.content = content
        self._elements = []
        self.is_block = is_block
        self.tag = tag
        self.folder = folder
        self._result = None
        if self.is_block:
            self.parse_inline()

    def __str__(self):
        wrapper = MARKDOWN.get(self.tag)
        # 代码块中嵌套```  ``` 会出现显示错乱问题
        re_block_code = re.compile("```([\s\S]*?)```", re.I)
        if self.tag == 'block_code' and re_block_code.search(self.content):
            _contents = ['\t' + content for content in self.content.split('\n')]
            self._result = '\n' + '\n'.join(_contents)
        else:
            if self.tag != 'code':
                self.content = filterTags(self.content)
                # 添加google翻译
                # self.content = self.trans.translate_break_url(self.content)
                # time.sleep(0.5)
            self._result = '{}{}{}'.format(wrapper[0], self.content, wrapper[1])

        return self._result

    def parse_inline(self):
        self.content = self.content.replace('\r', '')  # windows \r character
        self.content = self.content.replace('\xc2\xa0', ' ')  # no break space
        self.content = self.content.replace('&quot;', '\"')  # html quote mark

        for m in re.finditer("<img(.*?)en_todo.*?>", self.content):
            # remove img and change to [ ] and [x]
            # evernote specific parsing
            imgSrc = re.search('src=".*?"', m.group())
            imgLoc = imgSrc.group()[5:-1]  # remove source and " "
            imgLoc = imgLoc.replace('\\', '/')  # \\ folder slash rotate
            if os.stat(self.folder + "/" + imgLoc).st_size < 250:
                self.content = self.content.replace(m.group(), "[ ] ")
            else:
                self.content = self.content.replace(m.group(), "[x] ")

        if "e_" in self.tag:  # evernote-specific parsing
            for m in re.finditer(BlOCK_ELEMENTS['table'], self.content, re.I | re.S | re.M):
                # hmm can there only be one table?
                inner = Element(start_pos=m.start(),
                                end_pos=m.end(),
                                content=''.join(m.groups()),
                                tag='table', folder=self.folder,
                                is_block=True)
                self.content = inner.content
                return  # no need for further parsing ?

            # if no table, parse as usual
            self.content = self.content.replace('<hr/>', '\n---\n')
            self.content = self.content.replace('<br/>', '')

        if self.tag == "table":  # for removing tbody
            self.content = re.sub(INLINE_ELEMENTS['tbody'], '\g<1>', self.content)

        INLINE_ELEMENTS_LIST_KEYS = list(INLINE_ELEMENTS.keys())
        INLINE_ELEMENTS_LIST_KEYS.sort()
        for tag in INLINE_ELEMENTS_LIST_KEYS:
            pattern = INLINE_ELEMENTS[tag]
            if tag == 'a':
                self.content = re.sub(pattern, r'[\g<2>](\g<1>)', self.content)
            elif tag == 'img':
                self.content = re.sub(pattern, r'![\g<2>](\g<1>)\n', self.content)
            elif tag == 'img_single':
                self.content = re.sub(pattern, r'![](\g<1>)\n', self.content)
            elif tag == 'img_single_no_close':
                self.content = re.sub(pattern, r'![](\g<1>)\n', self.content)
            elif self.tag == 'ul' and tag == 'li':
                self.content = re.sub(pattern, r'- \g<1>\n', self.content)
            elif self.tag == 'ol' and tag == 'li':
                self.content = re.sub(pattern, r'1. \g<1>\n', self.content)
            elif self.tag == 'thead' and tag == 'tr':
                self.content = re.sub(pattern, r'\g<1>|\n', self.content.replace('\n', ''))
                self.process_thead_table()
            elif self.tag == 'tr' and tag == 'th':
                self.content = re.sub(pattern, r'|\g<1>|', self.content.replace('\n', ''))
                self.content = self.content.replace("||", "|")
                self.content = self.content.replace("|      |", "|")
            elif self.tag == 'tr' and tag == 'td':
                self.content = re.sub(pattern, r'|\g<1>|', self.content.replace('\n', ''))
                self.content = self.content.replace("||", "|")
                self.content = self.content.replace("|      |", "|")
            elif self.tag == 'table' and tag == 'td':
                self.content = re.sub(pattern, r'|\g<1>|', self.content)
                self.content = self.content.replace("||", "|")  # end of column also needs a pipe
                self.content = self.content.replace('|\n\n', '|\n')  # replace double new line
                self.construct_table()
            else:
                wrapper = MARKDOWN.get(tag)
                if tag == "strong":
                    self.content = re.sub(pattern, r'{}\g<2>{}'.format(wrapper[0], wrapper[1]), self.content)
                else:
                    self.content = re.sub(pattern, r'{}\g<1>{}'.format(wrapper[0], wrapper[1]), self.content)
        if self.tag == "e_p" and self.content[-1:] != '\n' and len(self.content) > 2:
            # focusing on div, add new line if not there (and if content is long enough)
            self.content += '\n'

    def process_thead_table(self):
        temp = self.content.split('\n', 3)
        count = 1
        for elt in temp:
            if elt != "":
                count = elt.count("|")  # count number of pipes
                break
        pipe = "|"  # beginning \n for safety
        for i in range(count - 1):
            pipe += ":----:|"
        pipe += "\n"
        self.content = self.content + pipe

    def construct_table(self):
        # this function, after self.content has gained | for table entries,
        # adds the |---| in markdown to create a proper table

        temp = self.content.split('\n', 3)
        count = 1
        for elt in temp:
            if elt != "":
                count = elt.count("|")  # count number of pipes
                break
        pipe = "\n|"  # beginning \n for safety
        for i in range(count - 1):
            pipe += "---|"
        pipe += "\n"

        self.content = pipe + pipe + self.content + "\n"  # TODO: column titles?
        self.content = self.content.replace('|\n\n', '|\n')  # replace double new line
        self.content = self.content.replace("<br/>\n", "<br/>")  # end of column also needs a pipe


class Tomd:
    def __init__(self, html='', folder='', file='', options=None):
        self.html = html  # actual data
        self.folder = folder
        self.file = file
        self.options = options  # haven't been implemented yet
        self._markdown = self.convert(self.html, self.options)

    def convert(self, html="", options=None):
        if html == "":
            html = self.html
        # main function here
        elements = []
        for tag, pattern in BlOCK_ELEMENTS.items():
            for m in re.finditer(pattern, html, re.I | re.S | re.M):
                # now m contains the pattern without the tag
                element = Element(start_pos=m.start(),
                                  end_pos=m.end(),
                                  content=''.join(m.groups()),
                                  tag=tag,
                                  folder=self.folder,
                                  is_block=True)
                can_append = True
                for e in elements:
                    if e.start_pos < m.start() and e.end_pos > m.end():
                        can_append = False
                    elif e.start_pos > m.start() and e.end_pos < m.end():
                        elements.remove(e)
                if can_append:
                    elements.append(element)
        elements.sort(key=lambda element: element.start_pos)
        self._markdown = ''.join([str(e) for e in elements])
        for index, element in enumerate(DELETE_ELEMENTS):
            self._markdown = re.sub(element, '', self._markdown)
        return self._markdown

    @property
    def markdown(self):
        self.convert(self.html, self.options)
        return self._markdown

    def export(self, folder=False):
        if len(self.file) < 1:
            warnings.warn("file not specified, renamed to tmp.md")
            file = "tmp.md"
        else:
            file = self.file.replace('.html', '.md')  # rename to md
        if len(self.folder) < 2:
            warnings.warn("folder not specified, will save to pwd")
        elif not folder:
            file = self.folder + '/' + file
        else:  # if folder is specified
            file = str(folder) + '/' + file
        f = open(file, 'w')
        f.write(self._markdown)
        f.close()


_inst = Tomd()
convert = _inst.convert

if __name__ == '__main__':
    html = '''
    <div>
<table class="table is-striped is-bordered dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>subreddit</th>
      <th>dayofweek</th>
      <th>hourofday</th>
      <th>num_with_min_score</th>
      <th>total</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>funny</td>
      <td>1</td>
      <td>0</td>
      <td>909</td>
      <td>139737</td>
    </tr>
    <tr>
      <th>1</th>
      <td>funny</td>
      <td>1</td>
      <td>1</td>
      <td>898</td>
      <td>139737</td>
    </tr>
    <tr>
      <th>2</th>
      <td>funny</td>
      <td>1</td>
      <td>2</td>
      <td>841</td>
      <td>139737</td>
    </tr>
    <tr>
      <th>3</th>
      <td>funny</td>
      <td>1</td>
      <td>3</td>
      <td>736</td>
      <td>139737</td>
    </tr>
    <tr>
      <th>4</th>
      <td>funny</td>
      <td>1</td>
      <td>4</td>
      <td>568</td>
      <td>139737</td>
    </tr>
  </tbody>
</table>
</div>
    '''
    md = Tomd(html).markdown
    print(md)
