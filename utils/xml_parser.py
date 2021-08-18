from contextlib import suppress
import xml.etree.ElementTree as ElT
from googletrans import Translator
from . import List, Optional, Tuple


class ParseXML:
    def __init__(self, xml):
        self.translator = Translator()
        self.xml = xml

    def extract_search_pages_quantity(self) -> Optional[int]:
        parser = ElT.fromstring(self.xml).find('.//{*}biblio-search')
        if parser:
            return int(parser.attrib['total-result-count'])
        return None

    def extract_patents(self) -> List[dict]:
        patents_pubnum = []
        for patent in ElT.fromstring(self.xml).findall('.//{*}document-id'):
            pubnum = {f'{i.tag[i.tag.find("}") + 1:]}': f'{i.text}' for i in patent}
            patents_pubnum.append(pubnum)
        return patents_pubnum

    def extract_abstract(self) -> Tuple[str, str, str]:
        ab = 'null'
        with suppress(IndexError):
            parser = ElT.fromstring(self.xml).findall('.//{*}abstract')[0]
            abstract = parser.findall('./{*}p')[0].text
            if abstract is not None:
                ab = abstract.replace("'", '').replace('\u2002', ' ')
                ab = self.translator.translate(ab).text
        return self._extract_title(), ab, self._extract_applicant()

    def _extract_title(self) -> str:
        t = 'null'
        with suppress(IndexError):
            i = ElT.fromstring(self.xml).findall('.//{*}invention-title')[0].text
            if i is not None:
                t = self.translator.translate(
                    '{}'.format(i.replace("'", '').replace('\u2002', ' '))).text
        return t

    def _extract_applicant(self) -> str:
        a = 'null'
        with suppress(IndexError):
            ap_name = ElT.fromstring(self.xml).findall('.//{*}applicant-name')[0]
            ap = ap_name.findall('./{*}name')[0].text
            if ap:
                ap = ap.replace("'", '').replace('\u2002', ' ').upper()
                a = self.translator.translate(ap).text if not ap.isascii() else ap
        return a

    def extract_patent_family(self) -> Optional[List[str]]:
        with suppress(IndexError):
            pf = ElT.fromstring(self.xml).findall('.//{*}family-member//{*}publication-reference')
            if len(pf) > 1:
                pf_l = []
                for i in pf:
                    infos = [info.text for info in i.findall('./{*}document-id')[0] if info.text is not None]
                    pf_l.append(''.join((infos[:-1])))
                    # appends without date of publication
                pf_l.sort()
                return pf_l
        return None

    def checks_for_img(self) -> Optional[str]:
        with suppress(IndexError):
            parser = ElT.fromstring(self.xml)
            p = parser.findall('.//{*}document-instance[@desc="Drawing"]')[0]
            return p.attrib.get('link')
        return None