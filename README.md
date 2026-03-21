Tu je príklad zo strednej školy, kde v zadaní bolo :
* zašifrovaný text
* tabuľku s frekvenciou jednotlivých písmen
Základná otázka je či by bolo by možné dešifrovať ten text iba s frekvenčnou tabuľkou pre jednotlivé znaky, bez použitia bigramov a trigramov?

Riešenie iba z frekvenčnou tabuľkou na jednotlivé znaky nie je moc možné ako samostatný algoritmus. Áno, bolo by to možné — ale s dôležitým "ale".

**Samotná frekvenčná tabuľka nestačí na automatické dešifrovanie.** Dá sa ňou získať len **počiatočný odhad** mapovania (zoradí písmená šifrovaného textu podľa frekvencie a priradíš ich k písmenám referenčného jazyka). Problém je, že frekvencie mnohých písmen sú si veľmi blízke — napríklad `s`, `n`, `r`, `t`, `i` sú vo francúzštine všetky medzi 6–8 %, takže poradie nie je spoľahlivé a počiatočný odhad bude mať niekoľko zámien.

**Čo teda stredoškoláci v skutočnosti robili?** Frekvenčná tabuľka dáva len odrazový mostík — zorientovanie sa. Potom **manuálne skúšanie** a opravovanie: pozreť sa na čiastočne dešifrovaný text, uhádnuť konkrétne slovo podľa kontextu (napr. `_e` → `le`, trojpísmenové slovo s vysokou frekvenciou → `les` alebo `des`), a postupne opravovať mapovanie. To je práve tá "ručná" kryptoanalýza — kombinácia štatistiky a jazykového úsudku.

**Algoritmus bez bigramov by teda musel robiť to isté** — iba frekvenčné zoradenie dá skóre, podľa ktorého nevieme povedať či je výsledok správny alebo nie. Bigramy a trigramy sú v podstate *automatizácia toho jazykového úsudku* — nahrádzajú "aha, toto vyzerá ako francúzske slovo" matematickým skóre.

Takže záver: na strednej škole to bolo **možné preto, lebo to robil človek** s jazykovou intuíciou. Pre počítačový algoritmus bez bigramov by frekvenčná tabuľka nestačila — skončil by v lokálnom optime bez schopnosti rozpoznať, či sa blíži k správnemu riešeniu.
