from sentence_transformers import SentenceTransformer
from typing import List

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def split_text(text: str, chunk_size: int = 250, chunk_overlap: int = 0) -> List[str]:
    step = max(1, chunk_size - chunk_overlap)
    chunks = []
    for i in range(0, len(text), step):
        chunks.append(text[i:i + chunk_size])
    return chunks

def embed_texts(texts: List[str]) -> List[List[float]]:
    return embedding_model.encode(texts).tolist()


POLISH_HISTORY_DATA = """
Bitwa pod Grunwaldem (15 lipca 1410) – jedna z największych bitew średniowiecza.
Strony konfliktu: Królestwo Polskie i Wielkie Księstwo Litewskie pod wodzą króla Władysława II Jagiełły oraz wielkiego księcia Witolda, przeciw Zakonowi Krzyżackiemu dowodzonemu przez wielkiego mistrza Ulricha von Jungingena.
Przebieg: wojska polsko-litewskie rozbiły główne siły Zakonu, a sam wielki mistrz poległ.
Skutki: bitwa przesądziła o osłabieniu potęgi Zakonu Krzyżackiego i wzmocnieniu pozycji Polski i Litwy; w 1411 roku podpisano I pokój toruński.

Unia w Krewie (1385) – porozumienie łączące Królestwo Polskie i Wielkie Księstwo Litewskie, stanowiące początek unii personalnej pod rządami Władysława II Jagiełły.

Unia Lubelska (1569) – utworzenie Rzeczypospolitej Obojga Narodów, unii realnej Polski i Litwy z wspólnym sejmem i polityką zagraniczną.

Konstytucja 3 maja (1791) – pierwsza nowoczesna konstytucja w Europie, reforma ustroju mająca wzmocnić państwo.

Rozbiory Polski (1772, 1793, 1795) – podziały terytorium Rzeczypospolitej między Rosję, Prusy i Austrię, skutkujące utratą niepodległości.

Powstanie Warszawskie (1944) – zbrojne wystąpienie przeciw okupacji niemieckiej, symbol oporu, zakończone klęską i zniszczeniem miasta.

Tło bitwy pod Grunwaldem: napięcia polsko-krzyżackie narastały w XIV–XV w., m.in. wokół Żmudzi i Pomorza Gdańskiego. W 1409 wybuchło powstanie żmudzkie wspierane przez Litwę, a Zakon ogłosił wojnę Polsce. Obie strony prowadziły mobilizację sił i działania dyplomatyczne w Europie.

Siły i dowódcy: po stronie polsko-litewskiej źródła wskazują łącznie ok. 26–30 tys. żołnierzy (chorągwie polskie, litewskie, rusko-tatarskie, zaciężni). Po stronie Zakonu ok. 21–27 tys. (bracia rycerze, zaciężni z Niemiec i Czech, posiłki z Prus i Pomorza). Dowódcy: Władysław II Jagiełło – naczelny wódz, Witold – prowadzenie skrzydła litewskiego, Zyndram z Maszkowic – dowodzenie częścią chorągwi polskich; Zakon – Ulrich von Jungingen.

Przebieg starcia: początek walk około południa. Skrzydło litewskie wykonało odwrót (część historyków uznaje go za pozorowany), co rozciągnęło szyki krzyżackie. Chorągwie polskie nacierały na centrum i prawe skrzydło. W kluczowym momencie doszło do załamania linii Zakonu; wielki mistrz Ulrich von Jungingen poległ podczas próby kontruderzenia. Wojska polsko-litewskie przejęły inicjatywę i rozstrzygnęły bitwę.

Skutki bezpośrednie: zwycięstwo otworzyło drogę do marszu na Malbork. Oblężenie nie przyniosło upadku stolicy Zakonu, lecz I pokój toruński (1411) potwierdził osłabienie potęgi krzyżackiej i zobowiązał ich do wysokich kontrybucji. W kolejnych latach doszło do wojny głodowej (1414) i procesów międzynarodowych, które ograniczały wpływy Zakonu.

Znaczenie: Grunwald stał się symbolem zwycięstwa Polski i Litwy oraz jednym z filarów pamięci historycznej. W historiografii pojawiają się nazwy Tannenberg (niem.) i Žalgiris (lit.). Opisy bitwy znajdują się m.in. u Jana Długosza; współczesne badania archeologiczne i wojskowe uzupełniają wiedzę o przebiegu starcia.
"""

doc_splits = split_text(POLISH_HISTORY_DATA)