import xml.etree.ElementTree as ElT


class ParseXML:
    from typing import List, Optional, Union, Tuple

    def __init__(self, xml):
        self.xml = xml

    def extract_search_pages_quantity(self) -> Optional[int]:
        parser = ElT.fromstring(self.xml).find('.//{*}biblio-search')
        total_pages = parser.attrib.get('total-result-count')
        if parser and total_pages:
            return int(total_pages)

    def extract_patents(self) -> Optional[List[dict]]:
        if patents := ElT.fromstring(self.xml).findall('.//{*}document-id'):
            ps = []
            for patent in patents:
                p = {}
                for fields in patent:
                    key = fields.tag[fields.tag.find('}') + 1:]
                    value = fields.text
                    p.update({key: value})
                ps.append(p)
            return ps

    def extract_abstract(self) -> Tuple[str, str, Union[List[str]]]:
        parser = ElT.fromstring(self.xml)
        try:
            ab = parser.find('.//{*}abstract').find('./{*}p').text.replace("'", '')
        except AttributeError:
            ab = 'null'
        return self._extract_titles(), ab, self._extract_applicants()

    def _extract_titles(self) -> str:
        if titles := ElT.fromstring(self.xml).findall('.//{*}invention-title'):
            t = [
                'Lang={} '.format(i.attrib.get('lang')) + i.text.replace("'", '')
                for i in titles]
            for title in t:
                if 'Lang=en' in title:
                    return title.split(' ', maxsplit=1).pop().replace("'", '')
            return t.pop().split(' ', maxsplit=1).pop().replace("'", '')
        print(self.xml)
        return 'null'

    def _extract_applicants(self) -> Union[str, List[str]]:
        if not ElT.fromstring(self.xml).findall('.//{*}applicant-name'):
            return 'null'
        applicants = ElT.fromstring(self.xml).findall('.//{*}applicant[@sequence="1"]')
        a = [
            i.find('.//{*}name').text.replace("'", '').lower()
            for i in applicants]
        for applicant in a:
            if '[' not in applicant and len(a) > 1:
                a.remove(applicant)
        if len(a) < 2:
            return a.pop()
        return a

    def extract_patent_family(self) -> Union[bool, List[str]]:
        if self._no_patent_family():
            return False
        pf = []
        for i in ElT.fromstring(self.xml).findall('.//{*}family-member//{*}publication-reference'):
            infos = [info.text for info in i.find('.//{*}document-id')]
            pf.append(''.join(infos[:-1]))
            # appends without date of publication
        return pf

    def _no_patent_family(self) -> bool:
        if msg := ElT.fromstring(self.xml).find('.//{*}message'):
            if msg.text == 'No results found':
                return True
            # TODO: e se não houver?
        return False

    def checks_for_imgs(self) -> Optional[Tuple[int, str]]:
        parser = ElT.fromstring(self.xml)
        if p := parser.find('.//{*}document-instance[@desc="Drawing"]'):
            u = p.attrib.get('link')
            return int(p.attrib.get('number-of-pages')), u
        # TODO: e os outros tipos de imagens?
