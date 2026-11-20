"""Build the six-page AML313 article from frozen result files.

Usage: python report/build_report.py [--root PROJECT] [--render-only]
The default refreshes rapport.md from saved evidence, then renders rapport.pdf.
With --render-only, an edited rapport.md is rendered without regeneration.
No signal extraction, model fitting, or test selection happens here.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ("temporal_features.png", "spectra_envelope.png", "development_scores.png",
           "final_confusion.png", "ablation.png")
CLASSES = {"healthy": "Sain", "inner_race": "Bague interne", "outer_race": "Bague externe", "ball": "Bille"}
EXPERIMENTS = ("E1", "E2", "E3", "E4")
PAGE_BREAK = "<!-- PAGE BREAK -->"


def _read_evidence(root: Path) -> dict:
    release = root / "results"
    required = [release / "summary.csv", release / "selection.json",
                release / "development_metrics.json", release / "final_metrics.json",
                release / "final_bootstrap.json"]
    required += [release / "figures" / figure for figure in FIGURES]
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Article non généré : preuves manquantes : {missing}")
    summary = pd.read_csv(release / "summary.csv")
    expected = {(stage, experiment) for stage in ("development", "final") for experiment in EXPERIMENTS}
    if set(zip(summary.stage, summary.experiment)) != expected or len(summary) != 8:
        raise ValueError("summary.csv must contain exactly E1–E4 for development and final")
    selection = json.loads((release / "selection.json").read_text())
    development = json.loads((release / "development_metrics.json").read_text())
    final = json.loads((release / "final_metrics.json").read_text())
    bootstrap = json.loads((release / "final_bootstrap.json").read_text())
    return {"summary": summary, "selection": selection, "development": development,
            "final": final, "bootstrap": bootstrap}


def _pct(value: float) -> str:
    return f"{100 * value:.1f}%".replace(".", ",")


def _number(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _row(summary: pd.DataFrame, stage: str, experiment: str) -> pd.Series:
    return summary.loc[summary.stage.eq(stage) & summary.experiment.eq(experiment)].iloc[0]


def _score_table(summary: pd.DataFrame, stage: str) -> str:
    lines = ["| Essai | Exact. équilibrée | Exact. pondérée | Macro-F1 | Exact. par essai |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for experiment in EXPERIMENTS:
        row = _row(summary, stage, experiment)
        lines.append(f"| {experiment} | {_pct(row.balanced_accuracy)} | {_pct(row.accuracy)} | "
                     f"{_pct(row.macro_f1)} | {_pct(row.record_accuracy)} |")
    return "\n".join(lines)


def _ablation_text(summary: pd.DataFrame, stage: str) -> str:
    values = {experiment: float(_row(summary, stage, experiment).balanced_accuracy) for experiment in EXPERIMENTS}
    contrasts = [("E2 - E1", values["E2"] - values["E1"]),
                 ("E4 - E3", values["E4"] - values["E3"]),
                 ("E3 - E1", values["E3"] - values["E1"]),
                 ("E4 - E2", values["E4"] - values["E2"])]
    return "; ".join(f"{name} = {delta * 100:+.1f} points".replace(".", ",") for name, delta in contrasts) + "."


def _ci(bootstrap: dict, comparison: str) -> str:
    entry = bootstrap["comparisons"][comparison]
    low, high = entry["ci95"]
    return (f"{comparison.replace('_minus_', ' - ')} : {100 * entry['point_difference']:+.1f} points "
            f"[IC bootstrap 95 % : {100 * low:+.1f} ; {100 * high:+.1f}]").replace(".", ",")


def make_markdown(root: Path, evidence: dict) -> str:
    summary = evidence["summary"]
    selected = evidence["selection"]
    bootstrap = evidence["bootstrap"]
    final = evidence["final"]
    winner = selected["winner"]
    winner_dev = _pct(float(_row(summary, "development", winner).balanced_accuracy))
    winner_final = _pct(float(_row(summary, "final", winner).balanced_accuracy))
    n_dev = int(_row(summary, "development", "E1").n_recordings)
    n_final = int(_row(summary, "final", "E1").n_recordings)
    nw_dev = int(_row(summary, "development", "E1").n_windows)
    nw_final = int(_row(summary, "final", "E1").n_windows)
    params = "; ".join(f"{name} : profondeur {selected['selected'][name]['params']['max_depth'] or 'libre'}, "
                         f"feuille {selected['selected'][name]['params']['min_samples_leaf']}"
                         for name in EXPERIMENTS)
    raw = "; ".join(f"{name} {_pct(final[name]['raw_window']['accuracy'])}" for name in EXPERIMENTS)
    one_record = ", ".join(CLASSES.get(name, name) for name in bootstrap["single_recording_classes"])
    document = f"""# Mouhamedou Yahya Cheikh Med Vall

# 25239

# Diagnostic de défauts de roulement par vibration

**AML313 · Groupe 7 · Article scientifique court · 20 novembre 2026**

## Résumé

Nous comparons quatre diagnostics de roulements CWRU à partir de fenêtres vibratoires. La question est de savoir si dix caractéristiques spectrales et d'enveloppe améliorent trois indicateurs temporels, et si le diagnostic tient sur une charge réservée. Le développement compte {n_dev} enregistrements ({nw_dev} fenêtres) à 0, 1 et 2 HP ; le test final compte {n_final} enregistrements ({nw_final} fenêtres) à 3 HP. Le choix du développement est {winner}, avec une exactitude équilibrée hors pli de {winner_dev}. Sur la charge réservée, son exactitude équilibrée pondérée par essai est {winner_final}. Les scores ne démontrent pas à eux seuls un transfert vers une autre machine.

## 1. Question et données

Le sujet demande un état sain, une bague interne défectueuse, une bague externe défectueuse ou une bille défectueuse. Notre hypothèse initiale est modeste : les bandes d'enveloppe proches des fréquences de défaut peuvent aider, tandis que le changement de charge peut dégrader les scores. Aucun gain n'était exigé.

Quarante fichiers MAT officiels ont été audités : quatre sains et trente-six défauts, de diamètre 0,007, 0,014 ou 0,021 pouce. Chaque charge de 0 à 3 HP compte un sain et trois essais de chaque défaut. Les quarante empreintes de fichier et de signal sont distinctes ; aucune valeur non finie n'a été trouvée. Deux fichiers sains n'ont pas de vitesse MAT ; leur vitesse de table est signalée comme approximative [1–3].

| Charge (HP) | Sain | Interne | Externe | Bille | Usage |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0, 1, 2 | 3 | 9 | 9 | 9 | Développement |
| 3 | 1 | 3 | 3 | 3 | Test réservé |

**Limite de population.** Les empreintes différentes ne garantissent pas des roulements physiques indépendants. Les fichiers ne donnent ni dates des mesures ni chronologie entre essais.

{PAGE_BREAK}

## 2. Préparation et indicateurs temporels

Les fichiers sains sont identifiés à 48 kHz et ceux des défauts à 12 kHz [1, 3]. Un FIR causal Hamming passe-bas à 4 800 Hz utilise 161 coefficients à 48 kHz et 41 à 12 kHz. Les sains sont décimés par quatre. Les deux voies excluent 0,1 s après ce filtre, puis 0,1 s après le passe-bande. Les fenêtres complètes durent 1 s à 12 kHz, sans recouvrement. Le fragment final incomplet est écarté et compté. La réponse numérique du FIR est proche entre les deux voies, sans rendre identiques leurs acquisitions physiques.

Sur le signal centré de chaque fenêtre, **RMS** = √moyenne(x²), **kurtosis** = moment centré d'ordre quatre normalisé (Pearson, correction d'échantillon), et **facteur de crête** = max|x| / RMS. Une fenêtre dégénérée provoque une erreur. Ces trois variables alimentent E1 et E3 ; aucune charge, étiquette ou vitesse brute n'entre dans X.

![Figure 1. Indicateurs temporels : un point représente la médiane d'un essai du développement ; le trait rouge est la médiane de la classe.](../results/figures/temporal_features.png)

Dans cette figure du développement, les essais sains ont un RMS faible ; les défauts montrent des valeurs plus dispersées. Les distributions de kurtosis et de facteur de crête se recouvrent entre classes. L'unité d'accélération numérique n'est pas établie par les pages consultées. Les points représentent des essais, pas des fenêtres indépendantes.

La fréquence native est associée à la classe saine dans ce sous-ensemble. Malgré le filtrage commun, un résidu d'acquisition peut aider à distinguer sain et défaut ; cette confusion possible limite l'interprétation physique.

{PAGE_BREAK}

## 3. Spectre, BPFO/BPFI et enveloppe

Chaque spectre retire la moyenne, applique Hann, puis corrige l'amplitude par la somme des poids. Pour N = 12 000 points à fs = 12 000 Hz, l'espacement des raies est **Δf = fs/N = 1 Hz**. Hann élargit le lobe principal : 1 Hz n'est pas une garantie de séparation de deux pics. L'enveloppe perd 0,05 s à chaque bord ; ses 0,9 s donnent Δf ≈ 1,111 Hz.

Pour le roulement DE et une vitesse r en tr/min, **BPFO = 3,5848 × r/60** et **BPFI = 5,4152 × r/60** [4]. Le passe-bande Butterworth d'ordre 4 couvre 2–5 kHz et avance causalement sur chaque essai. L'enveloppe analytique est calculée sur la fenêtre fermée ; le diagnostic n'est disponible qu'à sa fin. Le filtre a une réponse contrôlée numériquement, mais la résonance optimale d'un roulement donné n'est pas prouvée.

![Figure 2. Vibration et enveloppe : une fenêtre de chaque classe du développement. Les lignes BPFO et BPFI viennent de la vitesse de l'essai.](../results/figures/spectra_envelope.png)

Les dix variables ajoutées sont quatre descripteurs de forme spectrale et six parts d'énergie d'enveloppe près des harmoniques 1–3 de BPFO/BPFI (±3 Hz). Elles sont calculées de la même façon pour toutes les classes. Les deux vitesses saines approximatives rendent leurs bandes moins sûres.

{PAGE_BREAK}

## 4. Validation et ablation sur le développement

La charge 3 HP a été isolée avant les modèles. Trois plis `GroupKFold` utilisent la charge comme supergroupe : chaque validation porte sur une charge entière, soit 10 essais, et l'apprentissage sur les deux autres. Toutes les fenêtres et les dérivés d'un essai restent ensemble. Les quatre expériences partagent les mêmes fenêtres et plis : **E1** arbre + trois variables ; **E2** arbre + treize ; **E3** forêt + trois ; **E4** forêt + treize.

La grille fixée contient profondeurs 3, 6 ou libre et feuilles minimales 1 ou 5 ; la forêt a 200 arbres et la graine 313. La moyenne des exactitudes équilibrées par pli, chaque essai ayant un poids total égal, choisit les paramètres. En cas d'égalité : arbre plus court, puis feuille plus grande ; E1 avant E2 avant E3 avant E4. Réglages retenus : {params}.

{_score_table(summary, 'development')}

![Figure 3. Scores hors pli du développement, chaque essai ayant le même poids total.](../results/figures/development_scores.png)

Différences de l'exactitude équilibrée : {_ablation_text(summary, 'development')} Ces scores ont servi à choisir les modèles. Après cette sélection, ils sont optimistes et ne constituent pas une estimation indépendante.

{PAGE_BREAK}

## 5. Transfert réservé à 3 HP

Après gel de la configuration, des empreintes, des variables et des réglages, les quatre expériences ont été réentraînées sur tout le développement. Le marqueur de consultation a été écrit avant l'extraction des fenêtres finales. Les dix essais de 3 HP n'ont servi ni à la grille ni au choix du gagnant.

{_score_table(summary, 'final')}

Les exactitudes **brutes** par fenêtre sont : {raw}. Le tableau principal pondère les fenêtres pour que chaque essai compte autant. L'« exactitude par essai » classe la moyenne des probabilités de ses fenêtres. Les deux unités de décision répondent à des questions différentes.

![Figure 4. Matrices de confusion finales par enregistrement, E1–E4 ; lignes réelles, colonnes prédites.](../results/figures/final_confusion.png)

E4 classe correctement les dix essais après agrégation, mais son rappel pondéré des fenêtres de bague externe est de {_pct(final['E4']['weighted_window']['recall_by_class']['outer_race'])}. L'agrégation masque donc certaines erreurs de fenêtre. Par rapport au développement, les écarts à 3 HP mêlent changement de charge, changement d'essai et possibles différences entre roulements.

{PAGE_BREAK}

## 6. Incertitude, limites et conclusion

Les ablations finales, en points d'exactitude équilibrée pondérée par essai, sont : {_ablation_text(summary, 'final')} Elles décrivent le test réservé ; elles ne déclenchent aucun nouveau choix de modèle.

![Figure 5. Ablation E1–E4 sur développement et test réservé ; le second tracé est descriptif.](../results/figures/ablation.png)

Le bootstrap apparié tire {bootstrap['n_bootstrap']} fois des **enregistrements** au sein de chaque classe et partage les tirages entre modèles. Exemples de différences : {_ci(bootstrap, 'E4_minus_E1')} ; {_ci(bootstrap, 'E4_minus_E3')}. La borne basse du premier intervalle vaut zéro : ce contraste ne garantit pas un gain strict. La classe {one_record} n'a qu'un essai à 3 HP : sa variabilité entre essais n'est pas estimable. Les intervalles ne couvrent pas le changement de machine.

La décision pratique reste bornée au banc CWRU étudié. Le taux d'erreurs par classe et les confusions guident l'examen d'un essai suspect ; aucune durée de vie restante ni seuil d'intervention n'a été estimé. Les défauts sont artificiels, les unités numériques et l'identité physique des roulements restent partiellement inconnues. Les résultats sont reproductibles avec le manifeste, les empreintes, la configuration gelée et la commande du dépôt.

### Références

[1] CWRU Bearing Data Center, [table des défauts DE à 12 kHz](https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data) et [table des essais sains](https://engineering.case.edu/bearingdatacenter/normal-baseline-data).

[2] CWRU, « Apparatus and Procedures », [description du banc](https://engineering.case.edu/bearingdatacenter/apparatus-and-procedures).

[3] Radtke et Bock, 2022, § 4.1.1, [PHM Society](https://papers.phmsociety.org/index.php/phme/article/download/3329/1947).

[4] CWRU, « Bearing Information », [facteurs DE](https://engineering.case.edu/bearingdatacenter/bearing-information).

[5] AML313, énoncé du mini-projet, sujet 7, p. 10 et grille p. 12.
"""
    return document


def _register_fonts() -> None:
    base = Path("/usr/share/fonts/liberation")
    for name, file in (("Liberation", "LiberationSans-Regular.ttf"),
                       ("Liberation-Bold", "LiberationSans-Bold.ttf"),
                       ("Liberation-Italic", "LiberationSans-Italic.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(base / file)))
    pdfmetrics.registerFontFamily("Liberation", normal="Liberation", bold="Liberation-Bold", italic="Liberation-Italic")


def _inline(value: str) -> str:
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r"<font name='Liberation-Bold'>\1</font>", value)
    value = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#16466f">\1</link>', value)
    return value


def _styles() -> dict:
    blue = colors.HexColor("#173b5b")
    slate = colors.HexColor("#253445")
    return {
        "identity": ParagraphStyle("identity", fontName="Liberation-Bold", fontSize=16, leading=19, textColor=blue, spaceAfter=3),
        "title": ParagraphStyle("title", fontName="Liberation-Bold", fontSize=20, leading=24, textColor=blue, spaceAfter=10),
        "h2": ParagraphStyle("h2", fontName="Liberation-Bold", fontSize=12.2, leading=15, textColor=blue, spaceBefore=6, spaceAfter=6),
        "h3": ParagraphStyle("h3", fontName="Liberation-Bold", fontSize=10.2, leading=13, textColor=blue, spaceBefore=5, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Liberation", fontSize=9.05, leading=12.25, textColor=slate, spaceAfter=7),
        "caption": ParagraphStyle("caption", fontName="Liberation-Italic", fontSize=8, leading=10, textColor=slate, spaceBefore=3, spaceAfter=8),
        "table": ParagraphStyle("table", fontName="Liberation", fontSize=8.0, leading=10, textColor=slate),
        "small": ParagraphStyle("small", fontName="Liberation", fontSize=8.0, leading=10.4, textColor=slate, spaceAfter=6),
    }


def _table(lines: list[str], styles: dict, width: float) -> Table:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    rows.pop(1)  # Markdown separator.
    cols = len(rows[0])
    data = [[Paragraph(_inline(cell), styles["table"]) for cell in row] for row in rows]
    table = Table(data, colWidths=[width / cols] * cols, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0f5")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#9ab2c3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _image(root: Path, line: str, styles: dict, max_width: float) -> list:
    match = re.fullmatch(r"!\[(.+)\]\((.+)\)", line)
    if not match:
        raise ValueError(f"invalid image Markdown: {line}")
    caption, relative = match.groups()
    path = (root / "report" / relative).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    raw_width, raw_height = ImageReader(str(path)).getSize()
    # Tall spectrum and confusion panels get the available page width while
    # retaining a readable aspect ratio.
    width = min(max_width, 485)
    height = width * raw_height / raw_width
    if path.name == "spectra_envelope.png":
        width = 420
        height = width * raw_height / raw_width
    elif path.name == "final_confusion.png":
        width = 390
        height = width * raw_height / raw_width
    elif path.name == "ablation.png":
        width = 380
        height = width * raw_height / raw_width
    graphic = Image(str(path), width=width, height=height, hAlign="CENTER")
    return [graphic, Paragraph(_inline(caption), styles["caption"])]


def _story(root: Path, markdown: str, styles: dict, width: float) -> list:
    story = []
    lines = markdown.splitlines()
    index = 0
    title_count = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line == PAGE_BREAK:
            story.append(PageBreak())
        elif line.startswith("!["):
            story.extend(_image(root, line, styles, width))
        elif line.startswith("| "):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(_table(table_lines, styles, width))
            story.append(Spacer(1, 9))
            continue
        elif line.startswith("### "):
            story.append(Paragraph(_inline(line[4:]), styles["h3"]))
        elif line.startswith("## "):
            story.append(Paragraph(_inline(line[3:]), styles["h2"]))
        elif line.startswith("# "):
            title_count += 1
            story.append(Paragraph(_inline(line[2:]), styles["identity"] if title_count <= 2 else styles["title"]))
        else:
            paragraph = [line]
            while index + 1 < len(lines) and lines[index + 1].strip() and not lines[index + 1].startswith(("#", "|", "![", "<!--")):
                index += 1
                paragraph.append(lines[index].strip())
            style = styles["small"] if re.match(r"\[\d+\]", line) else styles["body"]
            story.append(Paragraph(_inline(" ".join(paragraph)), style))
        index += 1
    return story


class Article(BaseDocTemplate):
    def __init__(self, path: Path):
        super().__init__(str(path), pagesize=A4, leftMargin=47, rightMargin=47,
                         topMargin=39, bottomMargin=42, title="Diagnostic de défauts de roulement par vibration",
                         author="Mouhamedou Yahya Cheikh Med Vall")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="article", frames=frame, onPage=self._page))

    def _page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#b7c9d6"))
        canvas.line(47, 31, A4[0] - 47, 31)
        canvas.setFont("Liberation", 7.5)
        canvas.setFillColor(colors.HexColor("#536a7b"))
        canvas.drawString(47, 20, "AML313 · Groupe 7 · CWRU")
        canvas.drawRightString(A4[0] - 47, 20, f"{doc.page} / 6")
        canvas.restoreState()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--render-only", action="store_true", help="Render edited rapport.md without regenerating text")
    args = parser.parse_args()
    root = args.root.resolve()
    report = root / "report"
    report.mkdir(parents=True, exist_ok=True)
    markdown_path = report / "rapport.md"
    pdf_path = report / "rapport.pdf"
    if not args.render_only:
        markdown_path.write_text(make_markdown(root, _read_evidence(root)), encoding="utf-8")
    markdown = markdown_path.read_text(encoding="utf-8")
    if markdown.count(PAGE_BREAK) != 5:
        raise ValueError("article must have six explicit pages")
    _register_fonts()
    document = Article(pdf_path)
    document.build(_story(root, markdown, _styles(), document.width))
    pages = len(PdfReader(str(pdf_path)).pages)
    if pages != 6:
        raise ValueError(f"layout overflow: expected 6 pages, rendered {pages}")
    print(f"Built {markdown_path} and {pdf_path} ({pages} pages)")


if __name__ == "__main__":
    main()
