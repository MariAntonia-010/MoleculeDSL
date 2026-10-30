"""Nomes em português (Brasil) usados na página.

Elementos: nomes adotados no Brasil (IUPAC/SBQ). Os quatro mais recentes
seguem as formas brasileiras correntes (nihônio, moscóvio, tenessino,
oganessônio), ainda sem grafia oficial única.
Espécies: substâncias elementares diatômicas pelo nome estequiométrico da
IUPAC (dioxigênio, di-hidrogênio...), com a fórmula ao lado.
"""

ELEMENTOS = (
    "Hidrogênio Hélio Lítio Berílio Boro Carbono Nitrogênio Oxigênio Flúor Neônio "
    "Sódio Magnésio Alumínio Silício Fósforo Enxofre Cloro Argônio Potássio Cálcio "
    "Escândio Titânio Vanádio Crômio Manganês Ferro Cobalto Níquel Cobre Zinco "
    "Gálio Germânio Arsênio Selênio Bromo Criptônio Rubídio Estrôncio Ítrio Zircônio "
    "Nióbio Molibdênio Tecnécio Rutênio Ródio Paládio Prata Cádmio Índio Estanho "
    "Antimônio Telúrio Iodo Xenônio Césio Bário Lantânio Cério Praseodímio Neodímio "
    "Promécio Samário Európio Gadolínio Térbio Disprósio Hólmio Érbio Túlio Itérbio "
    "Lutécio Háfnio Tântalo Tungstênio Rênio Ósmio Irídio Platina Ouro Mercúrio "
    "Tálio Chumbo Bismuto Polônio Astato Radônio Frâncio Rádio Actínio Tório "
    "Protactínio Urânio Netúnio Plutônio Amerício Cúrio Berquélio Califórnio Einstênio Férmio "
    "Mendelévio Nobélio Laurêncio Rutherfórdio Dúbnio Seabórgio Bóhrio Hássio Meitnério Darmstádtio "
    "Roentgênio Copernício Nihônio Fleróvio Moscóvio Livermório Tenessino Oganessônio"
).split()

ESPECIES = {
    "agua": "Água",
    "metano": "Metano",
    "amonia": "Amônia (azano)",
    "etanol": "Etanol",
    "acetona": "Propanona (acetona)",
    "acido_acetico": "Ácido etanoico (acético)",
    "ureia": "Ureia",
    "dioxido_carbono": "Dióxido de carbono",
    "benzeno": "Benzeno",
    "naftaleno": "Naftaleno",
    "pirrol": "Pirrol",
    "ciclohexano": "Ciclo-hexano",
    "acido_tartarico_meso": "Ácido meso-tartárico",
    "e_1_2_dicloroeteno": "(E)-1,2-dicloroeteno",
    "penta_2_3_dieno": "Penta-2,3-dieno",
    "amonio_por_ligacao_coordenada": "Íon amônio (ligação coordenada)",
    "hidrogenio": "Di-hidrogênio (H₂)",
    "oxigenio": "Dioxigênio (O₂)",
    "nitrogenio": "Dinitrogênio (N₂)",
    "cloro": "Dicloro (Cl₂)",
    "cloreto_de_hidrogenio": "Cloreto de hidrogênio",
    "peroxido_de_hidrogenio": "Peróxido de hidrogênio",
    "monoxido_de_carbono": "Monóxido de carbono",
    "metanol": "Metanol",
    "argonio": "Argônio (átomo isolado)",
    "neonio": "Neônio (átomo isolado)",
    "sodio_1mais": "Sódio(1+) (íon monoatômico)",
    "cloreto": "Cloreto (íon monoatômico)",
    "oxido": "Óxido (íon monoatômico)",
    "proton": "Hídron, H⁺ (íon monoatômico)",
    "cloreto_de_sodio": "Cloreto de sódio (sólido iônico)",
    "sodio_metalico": "Sódio metálico (sólido metálico)",
    "carbono_13": "Carbono-13 (isótopo, com configuração)",
    "agua_pesada": "Água pesada (D₂O, com deutério)",
    "cromo": "Crômio (exceção ao Aufbau: 3d⁵ 4s¹)",
    "ferro_2mais": "Ferro(2+) (íon de metal de transição)",
    "helio": "Hélio (átomo isolado)",
    "sodio_configuracao_completa": "Sódio-23 (configuração completa)",
    "cobre": "Cobre (exceção ao Aufbau: 3d¹⁰ 4s¹)",
    "ferro_56": "Ferro-56 (termo ⁵D₄)",
    "uranio_235": "Urânio-235 (configuração com 5f)",
    "cloreto_37": "Cloreto-37 (íon com isótopo)",
    "ozonio": "Trioxigênio (ozônio, O₃)",
    "berilio": "Dicloreto de berílio (BeCl₂)",
    "glicina_zwitterion": "Glicina (zwitterion)",
    "hidronio": "Íon oxidânio (hidrônio, H₃O⁺)",
    "hidroxido": "Íon hidróxido",
    "nitrato": "Íon nitrato",
    "sulfato": "Íon sulfato",
    "carbonato": "Íon carbonato",
    "cianato": "Íon cianato",
    "azida": "Íon azida (N₃⁻)",
    "nitronio": "Íon nitrônio (NO₂⁺)",
    "metano_deuterado": "Metano deuterado (CD₄)",
    "etanol_1_deuterado": "(1R)-(1-²H)etanol (regra CIP 2)",
    "propan_2_ol_d3": "Propan-2-ol com CD₃ (centro por isótopo)",
    "e_pent_2_eno": "(E)-pent-2-eno",
    "r_2_clorobutano": "(R)-2-clorobutano",
    "hexa_2_3_dieno": "(Ra)-hexa-2,3-dieno (eixo de aleno)",
    "cis_1_3_dimetilciclohexano": "cis-1,3-dimetilciclo-hexano",
    "radical_metila": "Radical metila (CH₃•)",
    "oxido_nitrico": "Monóxido de nitrogênio (NO•, radical)",
    "agua_trifluoreto_de_boro": "Água–trifluoreto de boro (coordenada)",
    "oxido_de_magnesio": "Óxido de magnésio (sólido iônico)",
    "acido_sulfuroso": "Ácido sulfuroso (S com valência 4)",
    "tiofosgenio": "Tiofosgênio (CSCl₂)",
    "germano": "Germano (GeH₄, com repetição x4)",
    "ciclobutadieno": "Ciclobutadieno (antiaromático)",
    "hexafluorofosfato": "Íon hexafluorofosfato (PF₆⁻)",
    "tetracloroaluminato": "Íon tetracloroaluminato (AlCl₄⁻)",
    "e_diazeno": "(E)-diazeno (E/Z em N=N)",
    "e_acetaldoxima": "(E)-acetaldoxima (E/Z em C=N)",
    "atomo_de_hidrogenio": "Átomo de hidrogênio (1s¹)",
    "dioxigenio_tripleto": "Dioxigênio tripleto (O₂, unpaired 2)",
    "metileno_tripleto": "Metileno tripleto (CH₂, carbeno)",
    "dioxido_de_nitrogenio": "Dióxido de nitrogênio (NO₂•)",
    "hidroperoxila": "Radical hidroperoxila (HOO•)",
    "etano_13c2": "Etano com dois ¹³C (2x atom 13C)",
    "cloreto_de_magnesio": "Cloreto de magnésio (sólido iônico)",
    "dioxido_de_silicio": "Dióxido de silício (rede covalente)",
    "cobre_metalico": "Cobre metálico (motivo Cu₃)",
    "imidazol": "Imidazol (aromático com dois N)",
    "ciclopropenila": "Cátion ciclopropenila (aromático, 2 e⁻ pi)",
    "ciclopentadienila": "Ânion ciclopentadienila (aromático, 6 e⁻ pi)",
    "tropilio": "Cátion tropílio (aromático, 6 e⁻ pi)",
    "etanimina": "Etanimina (tautomeria imina–enamina)",
    "piridin_2_ona": "Piridin-2-ona (tautomeria com a 2-hidroxipiridina)",
    "cation_alila": "Cátion alila (ressonância da carga +)",
    "enolato": "Enolato da acetona (ressonância da carga −)",
    "diaminoprata": "Íon diaminoprata, [Ag(NH₃)₂]⁺",
}
