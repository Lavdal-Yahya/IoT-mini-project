"""Render the requested English project explanation as a standalone PDF.

Uses only saved evidence for consistency checks. Does not retrain any model.
Run with ReportLab and pypdf: python report/build_rundown.py
"""
from __future__ import annotations
import csv
import html
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, LongTable, TableStyle
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'output/pdf/project_rundown.pdf'
AUTHOR="Mouhamedou Yahya Cheikh Med Vall ; Maryeim Mohamed T'Feil"
CONTENT=r"""
Your project investigates whether vibration measurements can identify a bearing's condition, and whether that diagnosis still works when the machine operates under a different load.

It combines signal processing with machine learning. The signal processing turns a long vibration recording into a small set of meaningful measurements. The machine learning uses those measurements to distinguish four conditions:

- Healthy bearing.
- Inner-race defect.
- Outer-race defect.
- Ball defect.

The selected model achieved **98.15% balanced accuracy on the reserved test load** and correctly diagnosed **all 10 test recordings after combining their window predictions**. Those results are promising, but the test is small and contains only one healthy recording. Understanding both the result and its limits is central to understanding the project.

The work belongs to AML313, group 7. This guide preserves the detailed English explanation requested in the conversation and complements the separate six-page scientific article.

# The physical problem and the scientific question

A bearing allows a shaft to rotate with low friction. In the type studied here, balls roll between an inner ring and an outer ring. These rings are also called **races**. A defect on a race or ball can produce repeated impacts as the bearing rotates. Those impacts affect the machine's vibration.

An accelerometer measures that vibration as a sequence of numbers over time. The challenge is that looking at those numbers directly does not immediately tell you which component is damaged. Rotation, load, noise and the mechanical structure all influence the signal.

The practical motivation is maintenance: a useful diagnosis could help someone investigate a machine before its condition becomes more serious. Our actual experiment addresses **recognising the bearing condition**. Predicting remaining life or deciding when maintenance must happen would require additional work and evidence.

The project has two connected scientific questions:

> Do spectral and envelope measurements add useful information beyond three simple vibration indicators? Does the resulting classifier work on a load excluded from model development?

This is **supervised learning**. During training, we have examples whose correct condition is already known. The model learns relationships between their measurements and those labels.

# The dataset and what was checked

The data comes from **Case Western Reserve University's Bearing Data Center**, commonly shortened to CWRU. Its experiments used a motor test stand, accelerometers and bearings with deliberately introduced defects. The recordings are provided as MATLAB `.mat` files. These are controlled laboratory faults, which matters when interpreting the results. [CWRU apparatus and procedures](https://engineering.case.edu/bearingdatacenter/apparatus-and-procedures)

We selected **40 recordings** from the drive-end bearing measurements. "Drive end", abbreviated **DE**, identifies the side of the motor and measurement channel used.

The selection includes three artificial defect diameters - 0.007, 0.014 and 0.021 inches - and keeps the outer-race defect position consistent at 6 o'clock. This limits additional variation in the experiment.

| Load condition | Healthy | Inner race | Outer race | Ball | Total |
| --- | --- | --- | --- | --- | --- |
| 0 HP | 1 | 3 | 3 | 3 | 10 |
| 1 HP | 1 | 3 | 3 | 3 | 10 |
| 2 HP | 1 | 3 | 3 | 3 | 10 |
| 3 HP | 1 | 3 | 3 | 3 | 10 |

Here, **HP identifies the load condition in horsepower**. The 0 HP condition still contains measurements from a rotating motor.

The three defect sizes provide variation within each fault class. The classifier's output remains one of the four conditions; defect size is not an additional prediction target.

Before training anything, we audited the files. This is an important part of the scientific work because incorrect metadata can invalidate otherwise correct calculations. The audit checked file identities, channel names, lengths, missing values, repeated samples, duplicates and rotational-speed information.

It established that:

- All 40 selected DE signals have distinct fingerprints.
- No selected signal contains a non-finite value.
- No recording was excluded.
- Two healthy recordings lack a measured speed in their MAT file. Their published approximate speeds are used and explicitly marked as approximate.
- A file containing additional signal keys is handled by selecting its own correct DE channel, rather than treating every array as a separate recording.

A **fingerprint**, or SHA-256 hash, identifies the exact bytes of a file or signal. It helps detect accidental changes and duplicates. Different fingerprints establish different digital signals; they do not establish that different physical bearings were used.

The [data audit](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/docs/data_audit.md) records these findings and their limitations.

# Sampling rates and comparable preparation

A particularly important discovery was the sampling-rate difference: the selected healthy recordings are treated as **48,000 samples per second**, while the faulty recordings are **12,000 samples per second**, based on the documented sources.

A sampling rate tells us how much real time each sample represents. Getting it wrong moves frequencies to the wrong locations and changes the meaning of the analysis.

We therefore analyse everything on a common **12 kHz** time grid. Before reducing the healthy signals from 48 kHz to 12 kHz, we filter out high-frequency content that could otherwise fold into lower frequencies. This unwanted folding is called **aliasing**.

A comparable low-pass filter is applied to the original 12 kHz signals as well. Its cutoff is **4.8 kHz**. This makes the digital preparation more consistent between the groups. It cannot eliminate every difference in the original acquisition systems.

# Recordings, windows and the validation split

The distinction between a **recording** and a **window** is essential:

| Term | Meaning in this project |
| --- | --- |
| Recording or trial | One complete source measurement from a particular test condition. |
| Window | A one-second segment extracted from a recording. |
| Feature vector | The three or thirteen measurements calculated from one window. |
| Window prediction | The classifier's diagnosis for that window. |
| Recording diagnosis | A diagnosis obtained by combining predictions across the recording's windows. |

A recording can produce several windows, but those windows share the same source and operating conditions. They are related observations.

That is why we established the data split **before comparing models**:

- **0, 1 and 2 HP:** development data.
- **3 HP:** reserved final test.

Within development, we use three validation rounds:

| Validation round | Train on | Validate on |
| --- | --- | --- |
| One | 0 and 1 HP | 2 HP |
| Two | 0 and 2 HP | 1 HP |
| Three | 1 and 2 HP | 0 HP |

This is implemented with **GroupKFold**, using the whole load condition as the grouping variable.

Each round asks whether a model trained on two loads works on the third. The final 3 HP load remains separate while these comparisons and choices happen.

This protects against **data leakage**: giving the model information during development that makes its evaluation artificially easy. If windows from one recording were randomly divided between training and validation, the model could encounter closely related pieces of the same source on both sides.

Our split keeps the whole recording together. The stronger grouping by load also holds out an operating condition. However, the dataset does not identify physical bearings well enough to guarantee that the same bearing was never measured at multiple loads.

# Constructing the one-second windows

Once the split is established, the preparation produces **one-second windows without overlap**. At 12 kHz, each window contains:

= 12,000 samples/second × 1 second = 12,000 samples.

Startup portions are excluded to avoid filter transients. The windows begin at approximately **0.2 seconds** into each recording. Incomplete fragments at the end are counted and excluded.

This produces:

- **268 development windows** from 30 recordings.
- **92 final-test windows** from 10 recordings.

The filters are causal: they use current and previous samples. Envelope extraction uses a complete window, so a prediction becomes available after that window closes. For the first retained window, that is around 1.2 seconds into the recording. The implemented scientific pipeline runs in batches; it does not include a deployed live sensor-acquisition system.

# The three baseline features

Each window is then converted into **features**. These are compact numerical descriptions of its behaviour. The baseline uses three time-domain features:

| Feature | Calculation | Intuition |
| --- | --- | --- |
| RMS | √mean(x²) | Overall vibration magnitude. |
| Kurtosis | Corrected Pearson kurtosis | How strongly extreme values contribute; useful for describing impulsive signals. |
| Crest factor | max(abs(x)) / RMS | How large the biggest peak is relative to the overall magnitude. |

The window's mean is subtracted before these calculations.

For intuition, two signals might have similar overall vibration strength but differ in whether that vibration is relatively steady or contains occasional large impacts. RMS alone might miss that distinction; kurtosis and crest factor can help describe it.

We use the **Pearson convention** for kurtosis, whose Gaussian reference is 3. A high kurtosis can indicate strong extreme values, but it does not identify their mechanical cause by itself.

The source's physical amplitude units are not sufficiently established in our audit, so we avoid presenting RMS values as confirmed `g` or `m/s²` measurements.

# FFT, bearing frequencies and the envelope

The enriched representation adds information from the **frequency domain**.

A time-domain signal tells us how vibration changes over time. A frequency-domain representation tells us which repeating components contribute to it. The **Fast Fourier Transform**, or FFT, calculates that representation.

For our one-second window:

= Δf = fs / N = 12,000 / 12,000 = 1 Hz.

This is the spacing between FFT bins.

We also apply a **Hann window** before the FFT to reduce spectral leakage - the spreading caused by analysing a finite piece of a signal. Hann broadens peaks, so a 1 Hz bin spacing does not guarantee that two physical components only 1 Hz apart can be distinguished.

Next come two bearing-specific frequencies:

- **BPFO:** ball-pass frequency associated with the outer race.
- **BPFI:** ball-pass frequency associated with the inner race.

For the CWRU drive-end bearing, the published factors give:

= BPFO = 3.5848 × RPM / 60

= BPFI = 5.4152 × RPM / 60

RPM means revolutions per minute; dividing by 60 gives revolutions per second. These factors belong to the specified bearing geometry. [CWRU bearing information](https://engineering.case.edu/bearingdatacenter/bearing-information)

For an easy illustrative calculation, at 1,800 RPM the shaft rotates 30 times per second. The expected frequencies would be approximately **107.5 Hz for BPFO** and **162.5 Hz for BPFI**.

These frequencies tell us where useful evidence might occur. They do not function as automatic labels. A peak near a theoretical frequency is evidence to interpret alongside the rest of the signal.

The **envelope** helps expose repeated impacts that modulate faster vibrations. One useful analogy is following changes in loudness rather than following every fast oscillation of a sound wave.

Our envelope calculation:

1. Keeps a fixed **2-5 kHz** vibration band.
2. Uses the Hilbert transform to calculate the envelope of each complete window.
3. Removes **0.05 seconds from each edge**, where estimation effects are less reliable.
4. Calculates the envelope spectrum.

After trimming, the envelope contains 0.9 seconds of usable data, giving:

= Δf (envelope) = 1 / 0.9 ≈ 1.111 Hz.

The fixed band was checked on development examples. We do not claim it is the optimal resonance band for every recording.

# What the thirteen features contain

The enriched model uses **13 features in total**:

| Feature group | Number |
| --- | --- |
| RMS, kurtosis, crest factor | 3 |
| Centroid and entropy of the raw spectrum | 2 |
| Centroid and entropy of the envelope spectrum | 2 |
| Envelope energy near three BPFO harmonics | 3 |
| Envelope energy near three BPFI harmonics | 3 |
| Total | 13 |

A **spectral centroid** describes where the spectrum's energy is concentrated. **Spectral entropy** describes how spread out that energy is.

A **harmonic** is a multiple of a frequency: the first, second and third harmonics of BPFO are BPFO, 2 × BPFO and 3 × BPFO. We calculate the share of envelope spectral energy within **±3 Hz** of each candidate harmonic.

Every window receives the same features, regardless of its true class. Both BPFO-related and BPFI-related measurements are calculated for every class, including healthy and ball-fault examples.

Class labels, recording IDs and load labels do not directly enter the model's feature matrix. Rotational speed does influence feature engineering because it positions the theoretical frequency bands. Applying this method to new data would therefore require suitable speed information.

The detailed conventions are in the [feature documentation](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/docs/features.md).

# The models, ablation and selection

We then compare **decision trees** and **random forests**.

A decision tree learns a sequence of threshold-based questions about the features. A branch might separate windows according to their RMS, then split again using another measurement. The thresholds are learned from labelled training examples.

A random forest combines **200 trees**, trained with variation in their sampled data and candidate features. Combining their outputs can capture patterns more robustly than relying on one tree.

To separate the effect of the representation from the effect of the classifier, we run four experiments:

| Experiment | Classifier | Features |
| --- | --- | --- |
| E1 | Decision tree | Three temporal features |
| E2 | Decision tree | All thirteen features |
| E3 | Random forest | Three temporal features |
| E4 | Random forest | All thirteen features |

E1 is the required baseline.

This arrangement is an **ablation study**. Comparing E2 with E1 examines feature enrichment while keeping the classifier family fixed. Comparing E4 with E3 does the same for the forest. Comparing E3 with E1 examines the classifier change using the baseline features.

Each experiment has a small, predefined tuning budget:

- Maximum tree depth: 3, 6 or unlimited.
- Minimum samples per leaf: 1 or 5.
- Forest size: fixed at 200 trees.
- Random seed: fixed at 313.

That gives six settings per experiment, assessed across three development folds: **72 development fits in total**.

The setting with the best mean development balanced accuracy is selected for each experiment. Predetermined rules resolve ties. E4 is then selected as the overall development winner. Its forest uses a maximum depth of 6 and a minimum leaf size of 1.

An important qualification is that the development folds helped choose these settings. Their resulting scores are therefore **optimistic selection scores**, rather than an independent estimate of performance.

# Freezing the experiment and running the final test

Before opening the final test, the project creates a **scientific freeze**: fingerprints of the relevant code, configuration, data identifiers, partitions, selected settings and environment.

The final evaluation requires this freeze and records that the test has been consulted. The four announced experiments are trained on all development data and evaluated in one final campaign at 3 HP.

A technical replay can check reproducibility. A newly invented model or feature tuned after seeing these results would require independent evaluation before it could support a new confirmed claim. The [protocol](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/docs/protocol.md) describes this boundary.

The resulting scores are:

| Experiment | Development BA | Final BA | Final recording diagnoses |
| --- | --- | --- | --- |
| E1 - tree, 3 features | 92.90% | 90.74% | 9/10 correct |
| E2 - tree, 13 features | 87.35% | 98.15% | 10/10 correct |
| E3 - forest, 3 features | 95.06% | 89.81% | 10/10 correct |
| E4 - forest, 13 features | 99.69% | 98.15% | 10/10 correct |

BA means balanced accuracy. Development scores were used for model selection.

There are several findings here. On development, enrichment **reduced the tree's score by 5.56 percentage points**, while **improving the forest's score by 4.63 points**. Extra features helped one classifier and hurt the other.

On the final test, E2 and E4 reached the same displayed balanced accuracy. We retain E4 because it was selected before the final test was read.

The ablation evaluates all ten additional features together. It cannot tell us how much of the gain comes specifically from envelope analysis alone.

# How to read the metrics correctly

To understand the reported percentages, we need to distinguish **accuracy**, **balanced accuracy** and **recording-level accuracy**.

Ordinary window accuracy counts how often a window receives the right label. However, recordings have different numbers of windows. Counting every window equally gives longer recordings more influence.

Our principal window metrics give each recording a total weight of one. A recording with ten windows gives each window weight 1/10; one with nine windows gives each weight 1/9.

These are **evaluation weights**. Training itself uses the window table without explicit recording or class reweighting.

Balanced accuracy then averages the four class recalls equally. Recall asks: of the examples belonging to this class, how many were correctly recognised?

For E4, the weighted final recalls are:

| Class | Recall |
| --- | --- |
| Healthy | 100% |
| Inner race | 100% |
| Outer race | 92.59% |
| Ball | 100% |

Their average is **98.15%**.

**Macro-F1** averages the class F1 scores. F1 combines recall with precision, which asks how often a prediction of a class is correct. E4's final macro-F1 is also **98.15% after rounding**; it is a different calculation from balanced accuracy.

E4's raw final window confusion matrix is:

| True / predicted class | Healthy | Inner race | Outer race | Ball |
| --- | --- | --- | --- | --- |
| Healthy | 9 | 0 | 0 | 0 |
| Inner race | 0 | 28 | 0 | 0 |
| Outer race | 0 | 0 | 26 | 2 |
| Ball | 0 | 0 | 0 | 27 |

There are **two incorrect windows**, both outer-race windows predicted as ball faults.

Counting windows directly gives 90/92, or **97.83% raw accuracy**. With equal total weight per recording, the accuracy is **97.78%**. Balanced accuracy is **98.15%** because it additionally gives the four classes equal importance.

Likewise, 26/28 = 92.86% is the raw outer-race recall, while **92.59%** is the recording-weighted recall. These differences come from the denominators and weighting rules.

For a whole-recording diagnosis, we average the four class probabilities across that recording's windows, then choose the class with the highest average probability. A few mistaken windows can therefore coexist with a correct recording diagnosis.

That explains how E4 can have two window errors and still classify **all ten recordings correctly**. The [saved results table](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/results/summary.csv) and detailed metrics preserve these different views.

# Uncertainty and what the result supports

We also estimate uncertainty rather than reporting only a single percentage.

E4 improves final balanced accuracy over E1 by **7.41 percentage points**. A paired bootstrap resamples the **recordings within each class**, 1,000 times. The same resampled recordings are used for both models, keeping the comparison paired.

The resulting 95% bootstrap interval for E4 minus E1 is:

= [0.00, 17.59] percentage points.

The observed gain is positive, but its lower bound reaches zero. This experiment therefore does not establish a strictly positive gain across the wider range of trials we might encounter.

Resampling recordings is important because neighbouring windows are dependent. Treating all 92 windows as independent experiments would exaggerate the amount of evidence available.

The most important limitations are:

- **Very few recordings.** The final test contains ten recordings, including only one healthy recording. Its healthy-class variability cannot be estimated from repeated independent healthy trials.
- **Possible physical dependence.** Different files or loads may involve the same physical bearing. The available identifiers cannot resolve this.
- **Artificial laboratory faults.** Performance on these faults does not establish performance on naturally developing damage in service.
- **Acquisition differences associated with class.** Healthy and faulty recordings have different native sampling rates. Common preparation reduces a digital difference but cannot guarantee removal of acquisition-related cues.
- **Two approximate speeds.** Their uncertainty affects the placement of BPFO/BPFI bands.
- **Development-score optimism.** The same folds helped tune and select the models.
- **A combined feature ablation.** The experiment does not isolate the contribution of envelope features individually.
- **One reserved load on one dataset.** This is evidence about transfer to 3 HP within the selected CWRU setup.

# Software, reproducibility and deliverables

The software is organised so that the scientific calculation and the presentation can be checked separately.

| Location | Purpose |
| --- | --- |
| data/ | Manifest, audit findings and saved split assignments. |
| configs/experiment.json | The experiment's fixed scientific parameters. |
| src/bearing_diagnosis/ | Acquisition, signal processing, feature extraction, training, evaluation and orchestration. |
| results/ | Published predictions, metrics, selection, freeze and figures. |
| tests/ | Checks for signal calculations, metrics, split boundaries and protocol safeguards. |
| report/ | The six-page article, this guide's generator and report sources. |
| presentation/ | Slide sources, oral notes, prepared questions, PowerPoint and web versions. |

The [architecture document](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/ARCHITECTURE.md) explains how these parts fit together. The roadmap governs the project's scope and milestones; tasks.md records the execution evidence.

The pipeline uses Python, NumPy, SciPy, pandas and scikit-learn. It runs locally on CPU. Python and package versions are locked so the results can be rebuilt consistently.

Reproducibility was checked in a separate Python environment and a clean Git clone. The replay rebuilt the features and retrained the frozen model settings, then recovered all **368 final window predictions** - four models times 92 windows - with matching labels and probability comparisons at a tolerance of 10^-12.

That verifies reproducibility under the checked environment. It does not create another independent physical experiment. The [reproducibility record](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/docs/reproducibility.md) states exactly what was checked.

For replaying the existing scientific result, the main command is:

= make reproduce

The project also has **32 scientific tests** covering calculations, evaluation, grouping and protocol protection.

The web presentation has a different role: it makes the saved experiment easier to explain. Apache ECharts displays the real measurements, comparisons, confusion matrices and uncertainty intervals. Its controls let the reader inspect different features, models and aggregation levels. The scientific model remains the one selected before the final test.

The web version also includes fullscreen navigation, oral notes and native chart animations that replay when entering a slide. Its numerical and interaction checks are separate from the scientific checks. Full live-browser visual review remains unavailable because browser control is disabled in Work.

The current deliverables are complete enough to study, reproduce and present the experiment: the code, published evidence, six-page article, slide versions, interactive website and prepared questions are available. **The remaining open milestone is the human rehearsal** of the ten-minute presentation and preparation for the five-minute question period.

For learning the project yourself, the most useful order is to follow the [web presentation, private](https://cwru-group7-vibration-lab.fuzzychest.chatgpt.site), read the [protocol](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/docs/protocol.md), and then work through the [prepared oral questions](https://github.com/Lavdal-Yahya/IoT-mini-project/blob/main/presentation/questions_reponses.md). Those questions concentrate on the distinctions you are most likely to need to defend: recordings versus windows, development versus final testing, raw versus weighted metrics, and a strong observed score versus evidence of wider generalisation.
"""


def inline(value):
    value=html.escape(value)
    value=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',value)
    value=re.sub(r'`([^`]+)`',r'<font name="Mono" size="9.4">\1</font>',value)
    return re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#08736e"><u>\1</u></link>',value)


def styles():
    base=dict(fontName='Sans',fontSize=10.5,leading=15.2,textColor=colors.HexColor('#23343f'),allowWidows=0,allowOrphans=0)
    return {
        'body':ParagraphStyle('body',**base,spaceAfter=7),
        'bullet':ParagraphStyle('bullet',**base,leftIndent=14,firstLineIndent=0,bulletIndent=1,spaceAfter=4),
        'heading':ParagraphStyle('guide-heading',fontName='Sans-Bold',fontSize=14.3,leading=19,textColor=colors.HexColor('#14545a'),spaceBefore=15,spaceAfter=8,keepWithNext=True),
        'title':ParagraphStyle('title',fontName='Sans-Bold',fontSize=28,leading=33,textColor=colors.HexColor('#173645'),spaceAfter=9),
        'subtitle':ParagraphStyle('subtitle',fontName='Sans',fontSize=12,leading=17,textColor=colors.HexColor('#556975'),spaceAfter=20),
        'identity':ParagraphStyle('identity',fontName='Sans-Bold',fontSize=16,leading=19,textColor=colors.HexColor('#173645'),spaceAfter=3),
        'quote':ParagraphStyle('quote',**base,backColor=colors.HexColor('#edf5f3'),borderPadding=9,spaceBefore=8,spaceAfter=14),
        'equation':ParagraphStyle('equation',fontName='Sans',fontSize=12,leading=20,alignment=TA_CENTER,textColor=colors.HexColor('#173645'),spaceBefore=4,spaceAfter=10),
    }


def data_table(lines,width):
    rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in lines]
    rows=[row for row in rows if not all(re.fullmatch(r':?-+:?',c) for c in row)]
    n=len(rows[0])
    ratios={2:[.32,.68],3:[.21,.36,.43],4:[.38,.18,.18,.26],5:[.34,.16,.17,.17,.16],6:[.19,.14,.19,.19,.14,.15]}[n]
    if rows[0][0]=='Feature group':ratios=[.83,.17]
    if rows[0][0]=='Class':ratios=[.75,.25]
    if rows[0][0]=='Validation round':ratios=[.28,.39,.33]
    widths=[width*r/sum(ratios) for r in ratios]
    rendered=[]
    for i,row in enumerate(rows):
        rendered.append([Paragraph(inline(c),ParagraphStyle(f'cell-{i}-{j}',fontName='Sans-Bold' if i==0 else 'Sans',fontSize=9.3,leading=13,textColor=colors.white if i==0 else colors.HexColor('#23343f'),alignment=TA_RIGHT if i>0 and j>0 and re.fullmatch(r'[0-9.,/% ]+',c) else TA_LEFT)) for j,c in enumerate(row)])
    t=LongTable(rendered,colWidths=widths,hAlign='LEFT',repeatRows=1,spaceBefore=3,spaceAfter=11)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173645')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f5f5'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#173645')),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#cdd9dc'))]))
    return t


class Guide(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=48,bottomMargin=46,title='Understanding the CWRU bearing diagnosis project',author=AUTHOR,subject='A detailed walkthrough of AML313 group 7: data, signal processing, models, validation and results')
        frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='guide',frames=[frame],onPage=self.decorate))
        self.section=0
    def decorate(self,canvas,doc):
        canvas.saveState();canvas.setFont('Sans',8);canvas.setFillColor(colors.HexColor('#60737d'))
        canvas.drawString(48,A4[1]-28,'AML313 / GROUP 7')
        canvas.drawRightString(A4[0]-48,A4[1]-28,'CWRU BEARING DIAGNOSIS')
        canvas.setStrokeColor(colors.HexColor('#d1dcdf'));canvas.setLineWidth(.4);canvas.line(48,35,A4[0]-48,35)
        canvas.drawString(48,23,'Detailed project walkthrough / English edition')
        canvas.drawRightString(A4[0]-48,23,str(doc.page));canvas.restoreState()
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='guide-heading':
            self.section+=1;key=f'section-{self.section}';self.canv.bookmarkPage(key);self.canv.addOutlineEntry(flowable.getPlainText(),key,0,False)


def main():
    fontdir=Path('/usr/share/fonts/liberation')
    for name,file in [('Sans','LiberationSans-Regular.ttf'),('Sans-Bold','LiberationSans-Bold.ttf'),('Sans-Italic','LiberationSans-Italic.ttf'),('Mono','LiberationMono-Regular.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
    pdfmetrics.registerFontFamily('Sans',normal='Sans',bold='Sans-Bold',italic='Sans-Italic',boldItalic='Sans-Bold')
    rows=list(csv.DictReader((ROOT/'results/summary.csv').open()))
    final=next(r for r in rows if r['stage']=='final' and r['experiment']=='E4')
    assert round(float(final['balanced_accuracy'])*100,2)==98.15
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    doc=Guide(OUTPUT);sty=styles()
    story=[Paragraph('Understanding the CWRU<br/>bearing diagnosis project',sty['title']),Paragraph('A detailed walkthrough from first principles',sty['subtitle'])]
    for line in ['Mouhamedou Yahya Cheikh Med Vall','25239',"Maryeim Mohamed T'Feil",'22087']:story.append(Paragraph(html.escape(line),sty['identity']))
    story.append(Spacer(1,17))
    lines=CONTENT.strip().splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('|'):
            block=[]
            while i<len(lines) and lines[i].strip().startswith('|'):block.append(lines[i]);i+=1
            story.append(data_table(block,doc.width));continue
        if line.startswith('# '):story.append(Paragraph(inline(line[2:]),sty['heading']))
        elif line.startswith('> '):story.append(Paragraph(inline(line[2:]),sty['quote']))
        elif line.startswith('= '):story.append(Paragraph(inline(line[2:]),sty['equation']))
        elif line.startswith('- '):story.append(Paragraph(inline(line[2:]),sty['bullet'],bulletText='•'))
        elif re.match(r'^\d+\. ',line):
            number,text=line.split('. ',1);story.append(Paragraph(inline(text),sty['bullet'],bulletText=number+'.'))
        else:story.append(Paragraph(inline(line),sty['body']))
        i+=1
    doc.build(story)
    pdf=PdfReader(str(OUTPUT));text='\n'.join(p.extract_text() or '' for p in pdf.pages)
    for required in ['Mouhamedou Yahya Cheikh Med Vall',"Maryeim Mohamed T'Feil",'25239','22087','97.83%','97.78%','92.59%','98.15%','368','bootstrap','human rehearsal']:assert required in text,required
    assert len(pdf.pages)>5
    print(f'Created {OUTPUT} ({len(pdf.pages)} pages, {len(text.split())} extracted words)')

if __name__=='__main__':main()
