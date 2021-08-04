import xml.etree.ElementTree as ElT
from typing import List, Union, Tuple


class ParseXML:

    def __init__(self, xml):
        self.xml = xml

    def extract_qntd_pages(self) -> int:
        parser = ElT.fromstring(self.xml).find('.//{*}biblio-search')
        p = parser.attrib.get('total-result-count')
        return int(p)

    def extract_pubnums(self) -> List[dict]:
        pubsnums = []
        for i in ElT.fromstring(self.xml).findall('.//{*}document-id'):
            pubnum = {}
            for i2 in i:
                key = i2.tag[i2.tag.find('}') + 1:]
                value = i2.text
                pubnum.update({key: value})
            pubsnums.append(pubnum)
        return pubsnums

    def extract_abstract(self) -> Tuple[str, str]:
        parser = ElT.fromstring(self.xml)
        try:
            a = parser.find('.//{*}abstract').find('./{*}p').text
        except AttributeError:
            a = 'null'
        t = self._extract_titles()
        return t, a

    def _extract_titles(self) -> str:
        titles = ElT.fromstring(self.xml).findall('.//{*}invention-title')
        t = ['Lang={} '.format(i.attrib.get('lang')) + i.text for i in titles]
        return ' | '.join(t)

    def extract_patent_family(self):
        if error := isinstance(self._no_patent_family(), str):
            return error
        p = ElT.fromstring(self.xml)
        patent_family = []
        for i in p.findall('.//{*}family-member//{*}publication-reference'):
            infos = [info.text for info in i.find('.//{*}document-id')]
            patent_family.append(''.join(infos[:-1]))
            # appends without date of publication
        return patent_family

    def _no_patent_family(self) -> Union[str, bool]:
        msg = 'No results found'
        try:
            r = ElT.fromstring(self.xml).find('.//{*}message').text
        except AttributeError:
            return False
        else:
            if r == msg:
                return msg
            return 'Unkown error'

    def checks_for_imgs(self) -> Union[Tuple[int, str], str]:
        parser = ElT.fromstring(self.xml)
        if p := parser.find('.//{*}document-instance[@desc="Drawing"]'):
            u = p.attrib.get('link')
            return int(p.attrib.get('number-of-pages')), u
