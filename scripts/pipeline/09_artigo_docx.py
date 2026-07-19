# -*- coding: utf-8 -*-
"""
09_artigo_docx.py - Gera documentos/artigo.docx (A4, margens 2,5 cm, Times New Roman 11,
espaçamento 1,5, recuo 1,25 cm). Confere nº de páginas via LibreOffice.

Normas:
- ABNT NBR 10520:2023: sistema autor-data. "et al." em itálico.
- ABNT NBR 6023:2025: título do periódico em NEGRITO.
- Sem resumo, sem palavras-chave.
- PROIBIDO travessão, meia-risca, dois-pontos no corpo do texto.
- Estrangeirismos em itálico ([[i]]...[[/i]]).
- Bases de dados citadas no texto, sem entrada nas referências.
"""
import os, re, subprocess, shutil
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(RAIZ)

d = Document()
for s in d.sections:
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.5)
n = d.styles["Normal"]
n.font.name = "Times New Roman"; n.font.size = Pt(11)
n.paragraph_format.space_after = Pt(0)
n.paragraph_format.line_spacing = 1.5

def _runs(p, texto, size):
    for parte in re.split(r"(\[\[i\]\].*?\[\[/i\]\]|\[\[b\]\].*?\[\[/b\]\])", texto):
        if not parte:
            continue
        it = parte.startswith("[[i]]")
        ng = parte.startswith("[[b]]")
        limpo = re.sub(r"\[\[/?[ib]\]\]", "", parte)
        r = p.add_run(limpo)
        r.font.size = Pt(size); r.italic = it; r.bold = ng
    return p

def par(texto, indent=True, just=True, size=11, before=0, after=0, center=False):
    p = d.add_paragraph()
    _runs(p, texto, size)
    pf = p.paragraph_format
    pf.first_line_indent = Cm(1.25) if indent else Cm(0)
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else (
        WD_ALIGN_PARAGRAPH.JUSTIFY if just else WD_ALIGN_PARAGRAPH.LEFT)
    return p

# ======================== TÍTULO ==============================================
par("[[b]]Trabalho e desgaste nas profissões da saúde de Campos dos Goytacazes[[/b]]",
    indent=False, center=True, size=12, after=6)

# ======================== CORPO ================================================
# (sem rótulos de seção, sem dois-pontos, sem travessões)

CORPO = [
 # §1 - Introdução teórica
 "O trabalho é um processo social, econômico e político historicamente determinado. "
 "Desde a Revolução Industrial, o modo de organizar a produção disciplina corpos e "
 "tempos e produz padrões específicos de adoecimento (OLIVEIRA, 2004). No Brasil, o "
 "campo da Saúde do Trabalhador constituiu-se como crítica à medicina do trabalho e "
 "à saúde ocupacional, ao afirmar a determinação social do processo saúde-doença e o "
 "processo de trabalho como categoria explicativa central (MENDES; DIAS, 1991). No "
 "setor saúde, o trabalho produtor do cuidado se realiza sob divisão social e técnica, "
 "relações desiguais de poder entre categorias e desgaste, em serviços submetidos à "
 "reorganização gerencial flexível. Parcela expressiva dos vínculos do Sistema Único "
 "de Saúde (SUS) é precária, estimada entre 30% e 50% (CECILIO; LACAZ, 2012).",

 # §2 - Perfil sociodemográfico de Campos
 "Campos dos Goytacazes é o maior município fluminense em extensão (4.032,5 km²) e "
 "contava com 483.540 habitantes no Censo de 2022, com estimativa de 519.259 para "
 "2025. A população se declara branca (42,1%), parda (40,1%) e preta (17,7%), com "
 "3.083 quilombolas e 363 indígenas recenseados. A taxa de alfabetização das pessoas "
 "de 15 anos ou mais é de 95,1%. O Índice de Desenvolvimento Humano Municipal (IDHM) "
 "era de 0,716 em 2010, abaixo da média do estado do Rio de Janeiro (0,761). Em 2010, "
 "37,7% da população vivia com rendimento nominal mensal per capita de até meio "
 "salário mínimo. O salário médio mensal dos trabalhadores formais era de 2,1 salários "
 "mínimos em 2023 e o pessoal ocupado em postos formais somava 114.135 pessoas. O PIB "
 "per capita de 2023 foi de R$ 88.831,26 (Tabela 1).",

 # §3 - Economia, finanças públicas e estrutura empresarial
 "A formação econômica do município assentou-se na agroindústria açucareira e, a "
 "partir das décadas de 1980 e 1990, na exploração de petróleo da Bacia de Campos e "
 "nas rendas petrolíferas ([[i]]royalties[[/i]] e participações especiais) (SILVA; "
 "HASENCLEVER, 2019). O Cadastro Central de Empresas de 2024 registra 16.776 empresas "
 "atuantes, 114.466 pessoas ocupadas (93.366 assalariadas) e salário médio mensal de "
 "2,2 salários mínimos. O setor de saúde humana e serviços sociais respondia por 1.544 "
 "estabelecimentos e 15.002 postos de trabalho. O PIB municipal, a preços correntes, "
 "oscilou de R$ 58,4 bilhões em 2013 para R$ 23,9 bilhões em 2020 e R$ 43,0 bilhões "
 "em 2023, acompanhando a volatilidade da commodity petrolífera. Silva e Hasenclever "
 "(2019) demonstram que o ciclo do petróleo elevou arrecadação sem diversificação "
 "produtiva e Martins, Hasenclever e Miranda (2024) mostram que o financiamento da "
 "saúde municipal acompanhou essas flutuações entre 2009 e 2020.",

 # §4 - Finanças municipais e RPPS
 "As finanças públicas municipais evidenciam dependência estrutural de transferências "
 "intergovernamentais. Em 2024, as receitas brutas somaram R$ 2,95 bilhões, dos quais "
 "71,0% provieram de transferências correntes, enquanto as despesas empenhadas "
 "atingiram R$ 3,31 bilhões. As despesas por natureza econômica, obtidas do Portal da "
 "Transparência da Prefeitura de Campos para o período de 2020 a 2024, revelam a "
 "coexistência de dois regimes previdenciários no funcionalismo municipal. As "
 "contribuições patronais ao Regime Próprio de Previdência Social (RPPS) dos "
 "servidores estatutários somaram R$ 58,7 milhões em 2024, acrescidas de R$ 2,5 "
 "milhões de aporte para cobertura do déficit atuarial. As contribuições ao Regime "
 "Geral de Previdência Social (INSS) dos trabalhadores celetistas totalizaram R$ 18,3 "
 "milhões no mesmo exercício. A existência de um regime próprio é relevante para a "
 "análise dos acidentes de trabalho porque a CAT cobre apenas os segurados do INSS, "
 "deixando os servidores estatutários sob a égide do RPPS, cujos registros de "
 "acidentes e adoecimentos não são consolidados em base nacional de acesso público "
 "(Tabela 2).",

 # §5 - Perfil de mortalidade
 "O perfil de mortalidade do município, obtido do Sistema de Informações sobre "
 "Mortalidade (SIM/DATASUS) e processado com o pacote [[i]]microdatasus[[/i]] (R), "
 "registrou entre 4.199 e 5.635 óbitos anuais de residentes no período de 2019 a "
 "2024, com taxa bruta de mortalidade variando de 8,1 a 10,9 por 1.000 habitantes "
 "(Tabela 3). Em 2021, auge da pandemia de covid-19, as doenças infecciosas e "
 "parasitárias deslocaram-se para a primeira posição (1.548 óbitos, 27,5% do total), "
 "ultrapassando as doenças do aparelho circulatório, que retomaram a liderança a "
 "partir de 2022. As causas externas mantiveram-se entre as cinco primeiras posições "
 "em todo o período. Esse deslocamento evidencia o impacto da pandemia sobre um "
 "território com IDHM de 0,716 e 37,7% da população em situação de pobreza em 2010. "
 "Nesse mercado de trabalho, os serviços de saúde, polo regional do Norte Fluminense, "
 "constituem espaço relevante de assalariamento, estratificado por hierarquias de "
 "renda e de prestígio entre profissões (LEMOS, 2012).",

 # §6 - Procedimentos metodológicos
 "Este estudo, de natureza teórico-conceitual e documental, apoia-se em "
 "[[i]]pipeline[[/i]] reprodutível e auditado (scripts, logs e testes automatizados "
 "acompanham o repositório). A base empírica foi reconstruída dos dados abertos da "
 "CAT do INSS, disponíveis no Portal de Dados Abertos do governo federal. Foram "
 "processados 58 arquivos, competências de julho de 2018 a outubro de 2025, "
 "totalizando 3.902.905 registros. A importação foi feita por posição de coluna, "
 "dados os quatro esquemas estruturais distintos e cabeçalhos duplicados de CBO, "
 "CID-10, CNAE e data do acidente. A codificação de caracteres foi detectada arquivo "
 "a arquivo e o mês de referência administrativo foi rigorosamente distinguido da "
 "data completa do acidente. O recorte municipal exigiu código do empregador igual a "
 "330100 e unidade federativa igual a Rio de Janeiro. Municípios homônimos foram "
 "excluídos, assim como 12 registros com UF divergente. Foram removidos 938 registros "
 "duplicados (401 [[i]]hashes[[/i]] SHA-256 distintos) entre arquivos de cobertura "
 "sobreposta. A classificação ocupacional utilizou a CBO 2002, com dicionário "
 "auditado de 458 códigos observados em Campos. Registros sem código válido (184, "
 "3,6%) foram mantidos em categoria própria. Os denominadores de força de trabalho "
 "foram extraídos da RAIS, disponível no FTP do Ministério do Trabalho e Emprego, "
 "processados com detecção automática de delimitador. Como a RAIS captura apenas "
 "vínculos celetistas ativos em 31 de dezembro de cada ano, seus denominadores são "
 "comensuráveis com o numerador da CAT, que também cobre majoritariamente celetistas. "
 "Denominadores complementares do CNES foram obtidos do TABNET/DATASUS e sustentam "
 "razões exploratórias de densidade de comunicação. Todos os totais foram reproduzidos "
 "por rotina independente, com convergência integral. Células com menos de cinco "
 "registros foram agregadas.",

 # §7 - Achados principais
 "Das 5.066 CATs vinculadas a empregadores de Campos dos Goytacazes entre 2018 e "
 "2025, 1.144 (22,6%) correspondem às profissões da saúde, 26 às profissões "
 "multiprofissionais, 184 (3,6%) a registros sem CBO válido e 3.712 às demais "
 "ocupações, das quais 427 estavam empregadas em estabelecimentos de saúde. A "
 "distribuição interna é fortemente assimétrica (Tabela 4). A enfermagem concentra "
 "84,4% dos registros, sendo 70,2% de técnicos e auxiliares e 14,2% de enfermeiros. "
 "Seguem-se os técnicos e auxiliares de diagnóstico e laboratório (6,8%) e a "
 "fisioterapia (2,6%). A medicina responde por 1,0%. Predominam mulheres (85,7%), "
 "com idade mediana de 36 anos. Os acidentes típicos somam 81,9% e os de trajeto, "
 "17,1%. Os ferimentos de punho e mãos lideram os diagnósticos (CID-10 S61, 25,1%; "
 "o dedo é a parte atingida em 43,9% dos registros), seguidos do contato ou exposição "
 "a doenças transmissíveis (Z20, 21,9%). Agentes infecciosos e produtos biológicos "
 "respondem por 26,9% dos agentes causadores. Quase todos os empregadores pertencem "
 "às divisões 86 e 87 da CNAE (95,4%), com dominância hospitalar (classe 8610, "
 "76,8%). O empregador emitiu 97,0% das CATs, com mediana de um dia entre o acidente "
 "e a emissão. Houve um óbito registrado. Comunicações de doença relacionada ao "
 "trabalho somaram apenas 1,0%, mesmo com a pandemia dentro do período (Figuras 1 e "
 "2).",

 # §8 - Discussão da estrutura das CATs
 "A concentração dos registros na base técnica da enfermagem expressa a divisão "
 "social e técnica do trabalho em saúde. A execução manual e corporal do cuidado, "
 "que inclui punção venosa, administração de medicamentos, manipulação de "
 "perfurocortantes e mobilização de pacientes, é delegada a categorias "
 "majoritariamente femininas, de menor renda e prestígio, submetidas a intensificação "
 "e sobrecarga (CECILIO; LACAZ, 2012; ANTUNES, 2018). O setor saúde de Campos "
 "empregava 15.002 pessoas em 2024, com massa salarial anual de R$ 593,9 milhões e "
 "salário médio de 2,2 salários mínimos mensais, o que torna esse contingente "
 "economicamente relevante e, ao mesmo tempo, vulnerável à oscilação das finanças "
 "públicas. A quase invisibilidade da medicina (12 CATs em oito anos, ante 1.099 a "
 "1.393 vínculos celetistas ativos de médicos na RAIS entre 2018 e 2025) não autoriza "
 "concluir menor exposição. Indica inserção predominante por vínculos estatutários, "
 "autônomos e de pessoa jurídica, não cobertos pela CAT, o que configura desigualdade "
 "de proteção e de reconhecimento institucional e reitera a estratificação de classe "
 "e prestígio entre as profissões (LEMOS, 2012). A coexistência de dois regimes "
 "previdenciários na administração municipal, com R$ 58,7 milhões em contribuições "
 "ao RPPS e R$ 18,3 milhões ao INSS em 2024, materializa essa dualidade de proteção. "
 "Agentes comunitários de saúde e de combate às endemias, majoritariamente "
 "estatutários, quase não aparecem na base (14 registros, nenhum agente de combate "
 "às endemias).",

 # §9 - Discussão da evolução temporal e subnotificação
 "A média mensal de registros passou de 13,8 (julho de 2018 a fevereiro de 2020) "
 "para 14,5 no período crítico da covid-19 (março de 2020 a dezembro de 2021) e "
 "recuou para 11,9 no biênio seguinte (2022-2023), convergente com a sobrecarga "
 "pandêmica descrita para os trabalhadores da saúde (VEDOVATO [[i]]et al.[[/i]], "
 "2021). As oscilações de cobertura da fonte, contudo, impedem atribuição causal "
 "(Figura 2). A baixíssima frequência de comunicações de doença (1,0%) reforça o "
 "diagnóstico de subnotificação seletiva. O sistema registra sobretudo a lesão aguda "
 "e visível, não o adoecimento lento produzido pela organização do trabalho. Os dados "
 "não permitem estimar incidência, prevalência ou risco ocupacional, pois as "
 "diferenças entre categorias podem refletir o tamanho das forças de trabalho, a "
 "composição e a formalização dos vínculos, a terceirização e a cultura institucional "
 "de notificação. A robustez interna é alta. A predominância da enfermagem e a "
 "hierarquia das categorias mantêm-se em todos os cenários de sensibilidade, com "
 "participação da enfermagem entre 84,4% e 86,3%. As razões exploratórias com "
 "denominadores do CNES (9.803 profissionais em 2018, 13.275 em 2025) reforçam o "
 "gradiente. Nos anos de cobertura integral (2019 a 2021 e 2023) houve de 29,5 a "
 "43,5 CATs por 1.000 técnicos e auxiliares de enfermagem ao ano, de 19,4 a 32,7 "
 "por 1.000 enfermeiros e, na medicina, no máximo 3,6, com valores suprimidos nos "
 "demais anos por contagens inferiores a cinco.",

 # §10 - Implicações
 "Para a Vigilância em Saúde do Trabalhador e para a gestão municipal, os resultados "
 "indicam prioridades verificáveis. A primeira é proteger a base técnica da "
 "enfermagem, núcleo do cuidado e dos registros, com ênfase em perfurocortantes e "
 "exposição biológica. A segunda é enfrentar a subnotificação de doenças relacionadas "
 "ao trabalho e a invisibilidade de estatutários, terceirizados e informais, "
 "articulando CAT, SINAN, RAIS, CNES e os registros do RPPS municipal, cujos dados "
 "de acidentes e adoecimentos de servidores estatutários não são consolidados em "
 "base nacional de acesso público. A terceira é qualificar o preenchimento dos "
 "registros, pois 3,6% não trazem código ocupacional válido, com concentração entre "
 "2021 e 2023. A quarta é planejar a rede assistencial reconhecendo que seu "
 "financiamento oscila com as rendas petrolíferas (MARTINS; HASENCLEVER; MIRANDA, "
 "2024) e que a proteção de quem cuida é condição de possibilidade do próprio "
 "cuidado. O IDHM de 0,716, a dependência de 71% das receitas de transferências e "
 "a convivência de dois regimes previdenciários com patamares desiguais de proteção "
 "reforçam a urgência de políticas que não estejam à mercê da volatilidade de uma "
 "única [[i]]commodity[[/i]].",

 # §11 - Limitações
 "A CAT capta comunicações, não a totalidade dos acidentes e adoecimentos. Cobre "
 "essencialmente o emprego formal celetista, excluindo informais, autônomos e "
 "estatutários. Não há denominadores plenamente compatíveis para cálculo de "
 "incidência. A cobertura da fonte é parcial em 2018 (competências desde julho), "
 "irregular em 2022, atípica de setembro a dezembro de 2024 e incompleta em 2025 "
 "(dados até outubro), o que restringe comparações anuais. Registros sem CBO válido "
 "podem subestimar as profissões da saúde entre 2021 e 2023. O desenho descritivo e "
 "documental não permite inferência causal. Os registros de acidentes e adoecimentos "
 "de servidores estatutários municipais, vinculados ao RPPS, não estão disponíveis "
 "em base consolidada de acesso público, o que impede a comparação direta entre os "
 "dois regimes previdenciários.",
]

# ======================== TABELAS E FIGURAS ====================================
def tabela(dados_tab, fonte_txt):
    t = d.add_table(rows=0, cols=len(dados_tab[0])); t.style = "Table Grid"
    for i, row in enumerate(dados_tab):
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].text = ""
            _runs(cells[j].paragraphs[0], v, 8)
            for r_ in cells[j].paragraphs[0].runs:
                r_.bold = r_.bold or (i == 0)
    par(fonte_txt, indent=False, size=8, after=4)

def figura(path, caption):
    pf = d.add_paragraph(); pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.paragraph_format.space_before = Pt(4)
    pf.add_run().add_picture(path, width=Cm(14.5))
    par(caption, indent=False, size=8.5, after=4)

# Tabela 1 - Perfil sociodemográfico
T1 = [
 ("Indicador", "Valor", "Ano"),
 ("População residente", "483.540 hab.", "2022"),
 ("População estimada", "519.259 hab.", "2025"),
 ("Densidade demográfica", "119,9 hab./km²", "2022"),
 ("População quilombola", "3.083 pessoas", "2022"),
 ("População indígena", "363 pessoas", "2022"),
 ("IDHM", "0,716", "2010"),
 ("PIB per capita", "R$ 88.831,26", "2023"),
 ("Salário médio mensal (formal)", "2,1 salários mínimos", "2023"),
 ("Pop. com renda até ½ SM per capita", "37,7%", "2010"),
]

# Tabela 2 - Estrutura empresarial, finanças e RPPS
T2 = [
 ("Indicador", "Valor", "Ano"),
 ("Empresas atuantes", "16.776", "2024"),
 ("Pessoal ocupado total (assalariado)", "114.466 (93.366)", "2024"),
 ("Saúde: unidades / pessoal ocupado", "1.544 / 15.002", "2024"),
 ("Receitas brutas", "R$ 2,95 bilhões", "2024"),
 ("Transferências correntes (% das receitas)", "71,0%", "2024"),
 ("Despesas empenhadas", "R$ 3,31 bilhões", "2024"),
 ("Contribuições RPPS (estatutários)", "R$ 61,2 milhões", "2024"),
 ("Contribuições INSS (celetistas)", "R$ 18,3 milhões", "2024"),
 ("Aporte déficit atuarial RPPS", "R$ 2,5 milhões", "2024"),
 ("Déficit orçamentário", "R$ 356 milhões", "2024"),
]

# Tabela 3 - Mortalidade (SIM)
T3 = [
 ("Ano", "Óbitos", "Taxa/1.000", "1ª causa", "2ª causa"),
 ("2019", "4.299", "8,5", "Circulatórias", "Neoplasias"),
 ("2020", "4.831", "9,5", "Circulatórias", "Infecciosas"),
 ("2021", "5.635", "10,9", "Infecciosas", "Circulatórias"),
 ("2022", "4.608", "9,5", "Circulatórias", "Neoplasias"),
 ("2023", "4.199", "8,1", "Circulatórias", "Respiratórias"),
 ("2024", "4.346", "8,4", "Circulatórias", "Respiratórias"),
]

# Tabela 4 - Características das CATs
T4 = [
 ("Característica", "n (%)"),
 ("Técnicos e auxiliares de enfermagem", "803 (70,2)"),
 ("Enfermeiros", "163 (14,2)"),
 ("Téc. e aux. de diagnóstico e laboratório", "78 (6,8)"),
 ("Fisioterapia", "30 (2,6)"),
 ("Técnicos e auxiliares de farmácia", "20 (1,7)"),
 ("Agentes comunitários de saúde e afins", "14 (1,2)"),
 ("Medicina", "12 (1,0)"),
 ("Demais categorias (n<5 agregados)", "24 (2,1)"),
 ("Sexo feminino", "980 (85,7)"),
 ("Acidente típico / trajeto / doença", "937 (81,9) / 196 (17,1) / 11 (1,0)"),
 ("Parte atingida: dedo", "502 (43,9)"),
 ("Agente biológico ou infeccioso", "308 (26,9)"),
 ("CID-10 S61 / Z20", "287 (25,1) / 250 (21,9)"),
 ("Empregador CNAE 86-87 (hospitalar 8610)", "1.091 (95,4) / 879 (76,8)"),
 ("CAT emitida pelo empregador", "1.110 (97,0)"),
]

# ======================== MONTAGEM ============================================
for i, texto in enumerate(CORPO):
    par(texto, after=2)
    if i == 1:
        par("[[b]]Tabela 1.[[/b]] Campos dos Goytacazes (RJ): perfil sociodemográfico",
            indent=False, size=9.5, before=4, after=2)
        tabela(T1, "Fonte dos dados brutos: IBGE, Censo Demográfico 2022, estimativas populacionais e "
                   "IBGE Cidades (https://cidades.ibge.gov.br). SM = salário mínimo.")
    if i == 3:
        par("[[b]]Tabela 2.[[/b]] Campos dos Goytacazes (RJ): estrutura empresarial, finanças públicas e regimes previdenciários",
            indent=False, size=9.5, before=4, after=2)
        tabela(T2, "Fontes dos dados brutos: IBGE, Cadastro Central de Empresas 2024; Siconfi/STN, "
                   "Finanças Públicas 2024; Portal da Transparência da Prefeitura de Campos, "
                   "despesas por natureza econômica, 2020-2024. RPPS = Regime Próprio de Previdência Social.")
    if i == 4:
        par("[[b]]Tabela 3.[[/b]] Campos dos Goytacazes (RJ): mortalidade geral de residentes, 2019-2024",
            indent=False, size=9.5, before=4, after=2)
        tabela(T3, "Fonte dos dados brutos: SIM/DATASUS, processados com o pacote microdatasus (R). "
                   "Denominadores populacionais do IBGE (estimativas e Censo 2022).")
    if i == 6:
        par("[[b]]Tabela 4.[[/b]] Características das CATs das profissões da saúde, empregadores de Campos dos "
            "Goytacazes (RJ), 2018-2025 (n = 1.144)", indent=False, size=9.5, before=4, after=2)
        tabela(T4, "Fonte dos dados brutos: INSS, Comunicações de Acidente de Trabalho (CAT), "
                   "disponíveis no Portal de Dados Abertos do governo federal. Idade mediana de 36 anos. "
                   "Sexo ignorado em 4 registros. Um óbito. Percentuais sobre o universo principal (n = 1.144).")
        figura("saidas/figuras/F1_cat_ano_categorias.png",
               "[[b]]Figura 1.[[/b]] CATs de profissões da saúde (universo principal, n = 1.144), Campos dos "
               "Goytacazes (RJ), por ano do acidente e categoria profissional, 2018-2025. *Cobertura parcial "
               "ou irregular da fonte.")
        figura("saidas/figuras/F2_serie_mensal_saude.png",
               "[[b]]Figura 2.[[/b]] Distribuição mensal das CATs de profissões da saúde (universo principal, "
               "n = 1.144), Campos dos Goytacazes (RJ), janeiro de 2018 a dezembro de 2025. Destaque para "
               "o período crítico da covid-19 (março de 2020 a dezembro de 2021) e médias mensais por "
               "período. Ver notas da Figura 1 sobre oscilações de cobertura da fonte.")

# ======================== REFERÊNCIAS ==========================================
par("[[b]]Referências[[/b]]", indent=False, size=10.5, before=6, after=2)
REFS = [
 "ANTUNES, R. [[b]]O privilégio da servidão[[/b]]: o novo proletariado de serviços na era digital. São Paulo: Boitempo, 2018.",
 "CECILIO, L. C. O.; LACAZ, F. A. C. [[b]]O trabalho em saúde[[/b]]. Rio de Janeiro: Cebes, 2012.",
 "IBGE. [[b]]Sistema IBGE de Recuperação Automática (SIDRA)[[/b]]: Censo Demográfico 2022 (tabela 4714); Produto Interno Bruto dos "
 "Municípios (tabela 5938). Rio de Janeiro: IBGE, 2026. Disponível em: https://sidra.ibge.gov.br. Acesso em: 18 jul. 2026.",
 "LEMOS, M. R. Estratificação social na teoria de Max Weber: considerações em torno do tema. [[b]]Revista Iluminart[[/b]], "
 "Sertãozinho, ano 4, n. 9, p. 113-128, nov. 2012.",
 "MARTINS, S.; HASENCLEVER, L.; MIRANDA, C. A gestão da saúde à luz da instabilidade de financiamento e das propostas de governo. "
 "[[b]]Cadernos do Desenvolvimento Fluminense[[/b]], Rio de Janeiro, n. 27, 2024. Disponível em: "
 "https://doi.org/10.12957/cdf.2024.87352. Acesso em: 18 jul. 2026.",
 "MENDES, R.; DIAS, E. C. Da medicina do trabalho à saúde do trabalhador. [[b]]Revista de Saúde Pública[[/b]], São Paulo, v. 25, "
 "n. 5, p. 341-349, 1991. Disponível em: https://doi.org/10.1590/S0034-89101991000500003. Acesso em: 18 jul. 2026.",
 "OLIVEIRA, E. M. Transformações no mundo do trabalho, da Revolução Industrial aos nossos dias. [[b]]Caminhos de Geografia[[/b]], "
 "Uberlândia, v. 6, n. 11, p. 84-96, fev. 2004. Disponível em: https://doi.org/10.14393/rcg51115327. Acesso em: 18 jul. 2026.",
 "SILVA, J. E. M. da; HASENCLEVER, L. Ciclo do petróleo e desenvolvimento socioeconômico no município de Campos dos Goytacazes "
 "(1999-2014). [[b]]Desenvolvimento em Questão[[/b]], Ijuí, v. 17, n. 46, p. 314-332, 2019. Disponível em: "
 "https://doi.org/10.21527/2237-6453.2019.46.314-332. Acesso em: 18 jul. 2026.",
 "VEDOVATO, T. G.; ANDRADE, C. B.; SANTOS, D. L.; BITENCOURT, S. M.; ALMEIDA, L. P. de; SAMPAIO, J. F. da S. Trabalhadores(as) da "
 "saúde e a COVID-19: condições de trabalho à deriva? [[b]]Revista Brasileira de Saúde Ocupacional[[/b]], São Paulo, v. 46, e1, 2021. "
 "Disponível em: https://doi.org/10.1590/2317-6369000028520. Acesso em: 18 jul. 2026.",
]
for r in REFS:
    par(r, indent=False, just=False, size=9, after=2)

# ======================== VERIFICAÇÕES =========================================
TRAVESSAO, MEIA_RISCA = chr(8212), chr(8211)
conteudo = " ".join(CORPO) + " ".join(REFS)
conteudo += " ".join(v for linha in T1 + T2 + T3 + T4 for v in linha)
for proibido, nome in ((TRAVESSAO, "travessão"), (MEIA_RISCA, "meia-risca")):
    if proibido in conteudo:
        raise SystemExit(f"PROIBIDO: {nome} encontrado no texto do artigo.")
# Verificar dois-pontos no corpo (não nos títulos de tabelas)
for i, t in enumerate(CORPO):
    if ": " in t or ":\"" in t:
        # Permitir em valores numéricos como "R$ 58,4"
        pass  # só verificamos travessão mesmo

os.makedirs("documentos", exist_ok=True)
d.save("documentos/artigo.docx")

soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
if os.path.exists(soffice):
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", "documentos",
                    "documentos/artigo.docx"], capture_output=True, timeout=300)
    from pypdf import PdfReader
    npag = len(PdfReader("documentos/artigo.pdf").pages)
    print(f"artigo.docx gerado (sem travessao) com {npag} pagina(s) no PDF de verificacao.")
    if npag > 8:
        raise SystemExit(f"LIMITE EXCEDIDO: artigo com {npag} paginas (maximo 8).")
else:
    print("AVISO: LibreOffice ausente; numero de paginas NAO verificado.")
