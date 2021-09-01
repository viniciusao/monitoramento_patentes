from fpdf import FPDF
from pdf2image import convert_from_path
from monitor_patents_ops.bots import load_dotenv, environ, Queries, Tuple, Optional


class ReportMaker(FPDF):
    def __init__(self, quantity: int, **kwargs):
        super().__init__(**kwargs)
        self.summary = f'  Foram publicados {quantity} patentes nas classificações: {environ["IPC_CODES"]}. ' \
                       'Segue abaixo algumas estatísticas e patentes relevantes nas próximas páginas.'
        self.set_author('Vinícius Oliveira de Aguiar')
        self.title = 'Monitoramento de patentes - 01.01.2019 -> 04.08.2021'
        self.set_title(self.title)

    def set_summary_page(self) -> None:
        self.add_page()
        self._page_title('RESUMO')
        self.set_font('Times', '', 11)
        self.multi_cell(0, 5, txt=self.summary)
        self.ln()
        self.image('../files/statistics/br.jpg', 50, 70, 150)
        self.image('../files/statistics/mundo.jpg', 60, 190, 150)

    def _page_title(self, txt: str) -> None:
        self.set_font('helvetica', '', 13)
        self.set_fill_color(55, 255, 189)
        self.cell(0, 6, f'{txt}', 0, 1, 'C', True)
        self.ln(4)

    def print_page(self, txt: str, patent_info: Optional[Tuple[str]]) -> None:
        self.add_page()
        self._page_title(txt)
        self._patents_infos(patent_info)

    def _patents_infos(self, args: Optional[Tuple[str, ...]]) -> None:
        if args:
            country, pubnum, title, keywords, abstract, applicants, patent_family, image_path = args
            descriptions = eval(environ['DESCRIPTIONS'])
            self._img_pdf2jpg(image_path, country+pubnum)
            patent_info = (title, pubnum, keywords, abstract, applicants, patent_family)
            self._add_patent_info_page(self.epw / 4, descriptions, image_path, self.font_size * 2.5, patent_info)

    def header(self):
        self.image('../files/logo_boticario.png', 5, 0, 28)
        self.set_font('helvetica', 'B', 15)
        w = self.get_string_width(self.title) + 6
        self.set_x((290 - w) / 2)
        self.set_draw_color(161, 206, 252)
        self.set_fill_color(147, 252, 150)
        self.set_text_color(250, 130, 10)
        self.set_line_width(1)
        self.cell(w, 9, self.title, 1, 1, 'C', True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Página ' + str(self.page_no()), 0, 0, 'C')

    @staticmethod
    def _img_pdf2jpg(img: str, pubnum: str) -> None:
        if img != 'null':
            convert_from_path(f'../files/patents_imgs/{pubnum}.pdf',
                output_folder='../files/patents_imgs/', fmt='jpg',
                output_file=pubnum)

    def _add_patent_info_page(self, col_width: int, descriptions: Tuple[str], img: str, line_height: int, patent_info: Tuple[str, ...]) -> None:
        for d, pi in zip(descriptions, patent_info):
            self.set_font("Times", size=10)
            self.cell(col_width, 7, txt=f'**{d}: **', markdown=True)
            self.set_font("Times", size=9)
            if not pi.isascii():
                self.add_font('simli', fname='../utils/SIMLI.TTF', uni=True)
                self.set_font("simli", size=9)
            self.multi_cell(0, 7,  txt=pi, border='LTB')
            self.ln(line_height)
        self.set_font("Times", size=10)
        self.cell(col_width, 7, txt=f'**Imagem: **', markdown=True)
        if img != 'null':
            self.image(f'../files/patents_imgs/{patent_info[1]}0001-1.jpg',
                w=150, h=150)
        else:
            self.set_font("Times", size=9)
            self.multi_cell(0, 7, txt='Não há imagem.', border='LTB')


if __name__ == '__main__':
    load_dotenv()
    patents = Queries()
    rm = ReportMaker(len(patents.get_all_patents_infos()), orientation='portrait', format="A3")
    rm.set_summary_page()
    for p in patents.get_patents_keywords():
        rm.print_page('INFORMAÇÃO SOBRE A PATENTE', p)
    rm.output('../files/<file_name>.pdf')