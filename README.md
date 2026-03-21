Tu je príklad zo strednej školy, kde v zadaní bolo :
* zašifrovaný text
* tabuľku s frekvenciou jednotlivých písmen
Základná otázka je či by bolo by možné dešifrovať ten text iba s frekvenčnou tabuľkou pre jednotlivé znaky, bez použitia bigramov a trigramov?

Riešenie iba z frekvenčnou tabuľkou na jednotlivé znaky nie je moc možné ako samostatný algoritmus. Áno, bolo by to možné — ale s dôležitým "ale".

**Samotná frekvenčná tabuľka nestačí na automatické dešifrovanie.** Dá sa ňou získať len **počiatočný odhad** mapovania (zoradíš písmená šifrovaného textu podľa frekvencie a priradíš ich k písmen referenčného jazyka). Problém je, že frekvencie mnohých písmen sú si veľmi blízke — napríklad `s`, `n`, `r`, `t`, `i` sú vo francúzštine všetky medzi 6–8 %, takže poradie nie je spoľahlivé a počiatočný odhad bude mať niekoľko zámien.

**Čo teda stredoškoláci v skutočnosti robili?** Frekvenčná tabuľka im dala len odrazový mostík — zorientovanie sa. Potom **manuálne skúšali** a opravovali: pozreli sa na čiastočne dešifrovaný text, uhádli konkrétne slovo podľa kontextu (napr. `_e` → `le`, trojpísmenové slovo s vysokou frekvenciou → `les` alebo `des`), a postupne opravovali mapovanie. To je práve tá "ručná" kryptoanalýza — kombinácia štatistiky a jazykového úsudku.

**Algoritmus bez bigramov by teda musel robiť to isté** — iba frekvenčné zoradenie dá skóre, podľa ktorého nevieš povedať či je výsledok správny alebo nie. Bigramy a trigramy sú v podstate *automatizácia toho jazykového úsudku* — nahrádzajú "aha, toto vyzerá ako francúzske slovo" matematickým skóre.

Takže záver: na strednej škole to bolo **možné preto, lebo to robil človek** s jazykovou intuíciou. Pre počítačový algoritmus bez bigramov by frekvenčná tabuľka nestačila — skončil by v lokálnom optime bez schopnosti rozpoznať, či sa blíži k správnemu riešeniu.
