# def _patent_infos(self, patents_pubnum: list) -> None:
    #     for ppn in patents_pubnum:
    #         titles, a = self._get_abstract(ppn)
    #         pf = self._get_patent_family(ppn)
    #         imgs = self._check_for_images(ppn)
    #         print('Patente, Título, Abstract, Imgs =>',
    #               [ppn, titles, a, pf, imgs])
    #         sleep(4)
    #
    # def _get_abstract(self, pubnum: str):
    #     g = self._orch(*['search', '/biblio?', f'pn="{pubnum}"'])
    #     titles, a = g.extract_abstract()
    #     return titles, a

    # def _get_patent_family(self, pubnum: str):
    #     pf = self._orch(*['patent_family', pubnum]).extract_patent_family()
    #     if not pf:
    #         return pubnum
    #     return pf
    #
    # def _check_for_images(self, pubnum: str):
    #     if c := self._orch(*['check_for_imgs', pubnum]).checks_for_imgs():
    #         return self._get_imgs(c)
    #     return 'null'
    #
    # def _get_imgs(self, t_pages_and_url_piece: tuple):
    #     number_of_pages, url_fragment = t_pages_and_url_piece
    #     imgs = []
    #     for n, _ in enumerate(range(number_of_pages), start=1):
    #         imgs.append(self._encodeb64_img(url_fragment, n))
    #         sleep(1)
    #     return imgs

    # def _encodeb64_img(self, *args) -> bytes:
    #     from base64 import b64encode
    #
    #     url_fragment, page = args
    #     u = ''.join((
    #         os.getenv('OPS_RESTAPI_URL'), url_fragment, f'?Range={page}'))
    #     r = self._req(u, binary=True)
    #     return b64encode(r)