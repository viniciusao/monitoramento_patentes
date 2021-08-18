from itertools import zip_longest
from fuzzywuzzy import fuzz, process
from matplotlib import pyplot as plt
import numpy as np
from bots import load_dotenv, Queries, makedirs, cast, Tuple, List


load_dotenv()


class TopPlayerStatistics:
    def __init__(self) -> None:
        self.labels_br: List[str] = []
        self.labels_world: List[str] = []
        self.quantity_br: List[int] = []
        self.quantity_world: List[int] = []
        self.db = Queries()

    def main(self) -> None:
        top_players_br, top_players_world = self.db.get_patents_statistics()
        self._reorganize(top_players_br, top_players_world)
        labels = self._set_labels2compare(self.labels_br, self.labels_world)
        br2, br3, world2, world3 = labels
        if self.labels_br:
            self._do(self.labels_br, br2, br3, quantity=self.quantity_br,
                 chart_title="Top 10 Players BR", file_name='br')

        if self.labels_world:
            self._do(self.labels_world, world2, world3,
                     quantity=self.quantity_world, chart_title="Top 10 Players World",
                     file_name='world')

    def _do(self, *labels: list, quantity: list, chart_title: str, file_name: str) -> None:
        oficial_labels, labels2, labels3 = labels
        quantity = self._best_choices(*labels, quantity=quantity)
        oficial_labels, quantity = self._del_listelements(oficial_labels, labels2, quantity=quantity)
        oficial_labels, quantity = self._sort_labels_by_quantity(oficial_labels, quantity)
        self._generate_charts(oficial_labels, quantity, chart_title, file_name)

    def _reorganize(self, top_players_br: List[str], top_players_world: List[str]):
        for br, world in zip_longest(top_players_br, top_players_world):
            if br is None:
                self.labels_world.append(world[0])
                self.quantity_world.append(world[1])
                continue
            elif world is None:
                self.labels_br.append(br[0])
                self.quantity_br.append(br[1])
                continue
            self.labels_br.append(br[0])
            self.labels_world.append(world[0])
            self.quantity_br.append(br[1])
            self.quantity_world.append(world[1])

    @staticmethod
    def _set_labels2compare(*labels: list) -> Tuple[list, list, list, list]:
        labels_br, labels_world = labels
        labels_br2 = [(c, i) for c, i in enumerate(labels_br) if '[' not in i]
        labels_br3 = [i for i in labels_br if '[' in i]
        labels_world2 = [(c, i) for c, i in enumerate(labels_world) if '[' not in i]
        labels_world3 = [i for i in labels_world if '[' in i]
        return labels_br2, labels_br3, labels_world2, labels_world3

    @staticmethod
    def _best_choices(*labels: list, quantity: list) -> List[int]:
        oficial_labels, labels2, labels3 = labels
        for label in labels2:
            choices = process.extract(
                label[1].replace('CO., LTD.', '').replace('IP', '').replace(
                'CORPORATION', '').replace('BIOTECHNOLOGY', '').replace('COMPANY', '').replace('COSMETICS', '').replace('UNIVERSITY', '').replace('RESEARCH', '').replace('PHARMACEUTICAL', '').replace('MANAGEMENT', '').replace('TECHNOLOGY', '').replace('INTELLECTUAL', '').replace('PROPERTY', '').replace('PRODUCTS', '').replace('INDUSTRIAL', '').replace('INSTITUTE', '').replace('CHEMICAL', '').replace('LIMITED', '').replace('HEALTH', '').replace('PATENT', ''),
                labels3, scorer=fuzz.partial_token_set_ratio, limit=2)
            if choices[0][1] > 80 and choices[1][1] > 80:
                continue
            for company, score in choices:
                if score > 80:
                    quantity[oficial_labels.index(company)] += quantity[label[0]]
                    break
        return quantity

    @staticmethod
    def _del_listelements(*labels, quantity):
        oficial_labels, labels2 = labels
        for c, company in enumerate(labels2):
            del oficial_labels[company[0]-c]
            del quantity[company[0]-c]
        return oficial_labels, quantity

    @staticmethod
    def _sort_labels_by_quantity(labels: List[str], quantity: List[int]) -> Tuple[List[str], List[int]]:
        def order_by_qntd(x):
            return x.get('quantity')

        n = [{'company': a, 'quantity': b} for a, b in zip(labels, quantity)]
        n.sort(key=order_by_qntd, reverse=True)
        r_labels = [i.get('company') for i in n]
        r_quantity = [i.get('quantity') for i in n]
        return cast(List[str], r_labels), cast(List[int], r_quantity)

    @staticmethod
    def _generate_charts(labels: List, quantity: List, title: str, fname: str) -> None:
        plt.rcdefaults()
        fig, ax = plt.subplots()
        y_pos = np.arange(len(labels))
        ax.barh(y_pos, quantity, align='center')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel('Quantidade de patentes')
        ax.set_title(title)
        ax.bar_label(ax.containers[0])
        makedirs('../files/statistics/', exist_ok=True)
        plt.savefig(f'../files/statistics/{fname}.jpg', bbox_inches='tight')

if __name__ == '__main__':
    TopPlayerStatistics().main()