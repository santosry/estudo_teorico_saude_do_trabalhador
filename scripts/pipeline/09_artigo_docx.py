# -*- coding: utf-8 -*-
"""
09_artigo_docx.py - Gera documentos/artigo.docx (A4, margens 2,5 cm, Times New Roman 11,
espaçamento 1,5, recuo 1,25 cm). Confere nº de páginas via LibreOffice (limite: 10).

Normas:
- Citações: (Mendes e Dias, 1991), (Martins, Hasenclever e Miranda, 2024)
- "et al." em itálico.
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
        if not parte: continue
        it = parte.startswith("[[i]]"); ng = parte.startswith("[[b]]")
        limpo = re.sub(r"\[\[/?[ib]\]\]", "", parte)
        r = p.add_run(limpo); r.font.size = Pt(size); r.italic = it; r.bold = ng
    return p

def par(texto, indent=True, just=True, size=11, before=0, after=0, center=False):
    p = d.add_paragraph(); _runs(p, texto, size)
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
CORPO = [
 # §1 - Introdução teórica
 "O trabalho é um processo social, econômico e político historicamente determinado. "
 "Desde a Revolução Industrial, o modo de organizar a produção disciplina corpos e "
 "tempos e produz padrões específicos de adoecimento (Oliveira, 2004). No Brasil, o "
 "campo da Saúde do Trabalhador constituiu-se como crítica à medicina do trabalho e "
 "à saúde ocupacional, ao afirmar a determinação social do processo saúde-doença e o "
 "processo de trabalho como categoria explicativa central (Mendes e Dias, 1991). No "
 "setor saúde, o trabalho produtor do cuidado se realiza sob divisão social e técnica, "
 "relações desiguais de poder entre categorias e desgaste, em serviços submetidos à "
 "reorganização gerencial flexível. Parcela expressiva dos vínculos do Sistema Único "
 "de Saúde (SUS) é precária, estimada entre 30% e 50% (Cecilio e Lacaz, 2012).",

 # §2 - Formação histórica de Campos
 "A formação econômica de Campos dos Goytacazes estrutura-se em três grandes ciclos. "
 "O primeiro, açucareiro, remonta ao século XVIII e organizou o território sobre a "
 "grande propriedade monocultora e o trabalho escravizado. No século XIX, o município "
 "consolidou-se como o maior produtor nacional de açúcar, posição mantida até meados "
 "do século XX, quando o modelo entrou em prolongada decadência. O fechamento de "
 "usinas e a crise do setor sucroalcooleiro, a partir dos anos 1980, produziram "
 "desemprego em massa e reconfiguração da estrutura ocupacional. O segundo ciclo, "
 "petrolífero, iniciou-se com a descoberta da Bacia de Campos no final dos anos 1970 "
 "e consolidou-se nas décadas seguintes com a instalação da Petrobras e de empresas "
 "do setor [[i]]offshore[[/i]]. A partir de 1998, com a Lei do Petróleo (Lei nº "
 "9.478/1997), as rendas petrolíferas ([[i]]royalties[[/i]] e participações "
 "especiais) passaram a representar fração crescente das receitas municipais. O "
 "terceiro ciclo, em curso, caracteriza-se pela estagnação da atividade petrolífera, "
 "pelo declínio dos repasses a partir de 2014 e pela busca de alternativas econômicas, "
 "sem que a diversificação produtiva tenha se efetivado (Silva e Hasenclever, 2019).",

 # §3 - Perfil sociodemográfico
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

 # §4 - Economia e estrutura empresarial
 "A estrutura empresarial do município, captada pelo Cadastro Central de Empresas de "
 "2024, registra 16.776 empresas atuantes, 114.466 pessoas ocupadas (93.366 "
 "assalariadas) e salário médio mensal de 2,2 salários mínimos. O setor de saúde "
 "humana e serviços sociais respondia por 1.544 estabelecimentos e 15.002 postos de "
 "trabalho. O PIB municipal, a preços correntes, oscilou de R$ 58,4 bilhões em 2013 "
 "para R$ 23,9 bilhões em 2020 e R$ 43,0 bilhões em 2023, acompanhando a volatilidade "
 "do petróleo. Silva e Hasenclever (2019) demonstram que o ciclo petrolífero elevou "
 "arrecadação sem diversificação produtiva e Martins, Hasenclever e Miranda (2024) "
 "mostram que o financiamento da saúde municipal acompanhou essas flutuações entre "
 "2009 e 2020. A trajetória dos três ciclos econômicos - açúcar, petróleo e "
 "estagnação - produziu um mercado de trabalho segmentado, com a administração "
 "pública municipal como um dos principais empregadores, o que é relevante para a "
 "análise dos regimes previdenciários que coexistem no município (Tabela 2).",

 # §5 - Finanças municipais e duplo regime previdenciário
 "As finanças públicas municipais evidenciam dependência estrutural de transferências "
 "intergovernamentais. Em 2024, as receitas brutas somaram R$ 2,95 bilhões, das quais "
 "71,0% provieram de transferências correntes, enquanto as despesas empenhadas "
 "atingiram R$ 3,31 bilhões, resultando em déficit orçamentário de R$ 356 milhões. "
 "As despesas por natureza econômica, obtidas do Portal da Transparência da Prefeitura "
 "de Campos para o período de 2020 a 2024, revelam a coexistência de dois regimes "
 "previdenciários no funcionalismo municipal, com implicações diretas para a "
 "notificação de acidentes e adoecimentos. O Regime Próprio de Previdência Social "
 "(RPPS) cobre os servidores estatutários. As contribuições patronais ao RPPS "
 "somaram R$ 58,7 milhões em 2024, acrescidas de R$ 2,5 milhões de aporte para "
 "cobertura do déficit atuarial. O Regime Geral de Previdência Social (INSS) cobre "
 "os trabalhadores celetistas, com contribuições patronais de R$ 18,3 milhões no "
 "mesmo exercício. A razão entre as contribuições (RPPS/INSS = 3,3) indica a "
 "predominância do vínculo estatutário no orçamento de pessoal. Como a CAT é "
 "instrumento exclusivo do INSS, os acidentes e adoecimentos dos servidores "
 "estatutários, vinculados ao RPPS, não são capturados por essa fonte. Os registros "
 "de afastamentos de estatutários são geridos pelo instituto de previdência municipal "
 "(PREVICAMPOS) e não estão disponíveis em base consolidada de acesso público. Essa "
 "dualidade de regimes produz uma assimetria fundamental de visibilidade "
 "previdenciária. O que se conhece sobre acidentes de trabalho na saúde municipal de "
 "Campos refere-se majoritariamente aos celetistas, enquanto os estatutários "
 "permanecem institucionalmente invisíveis para o sistema nacional de registros "
 "(Tabela 3).",

 # §6 - Perfil de mortalidade
 "O perfil de mortalidade do município, obtido do Sistema de Informações sobre "
 "Mortalidade (SIM/DATASUS) e processado com o pacote [[i]]microdatasus[[/i]] (R), "
 "registrou entre 4.199 e 5.635 óbitos anuais de residentes no período de 2019 a "
 "2024, com taxa bruta de mortalidade variando de 8,1 a 10,9 por 1.000 habitantes "
 "(Tabela 4). Em 2021, auge da pandemia de covid-19, as doenças infecciosas e "
 "parasitárias deslocaram-se para a primeira posição (1.548 óbitos, 27,5% do total), "
 "ultrapassando as doenças do aparelho circulatório, que retomaram a liderança a "
 "partir de 2022. As causas externas mantiveram-se entre as cinco primeiras posições "
 "em todo o período. Esse deslocamento evidencia o impacto da pandemia sobre um "
 "território com IDHM de 0,716 e 37,7% da população em situação de pobreza em 2010. "
 "Nesse mercado de trabalho estratificado, os serviços de saúde, polo regional do "
 "Norte Fluminense, constituem espaço relevante de assalariamento, segmentado por "
 "hierarquias de renda e de prestígio entre profissões (Lemos, 2012).",

 # §7 - Procedimentos metodológicos
 "Este estudo, de natureza teórico-conceitual e documental, apoia-se em "
 "[[i]]pipeline[[/i]] reprodutível e auditado (scripts, logs e testes acompanham o "
 "repositório). A base empírica foi reconstruída dos dados abertos da CAT do INSS, "
 "disponíveis no Portal de Dados Abertos do governo federal. Foram processados 58 "
 "arquivos, competências de julho de 2018 a outubro de 2025, totalizando 3.902.905 "
 "registros. A importação foi feita por posição de coluna, dados os quatro esquemas "
 "estruturais distintos e cabeçalhos duplicados de CBO, CID-10, CNAE e data do "
 "acidente. O recorte municipal exigiu código do empregador igual a 330100 e unidade "
 "federativa igual a Rio de Janeiro. Foram removidos 938 registros duplicados (401 "
 "[[i]]hashes[[/i]] SHA-256 distintos) entre arquivos de cobertura sobreposta. A "
 "classificação ocupacional utilizou a CBO 2002, com dicionário auditado de 458 "
 "códigos observados em Campos. Os denominadores de força de trabalho foram extraídos "
 "da RAIS, disponível no FTP do Ministério do Trabalho e Emprego. Como a RAIS captura "
 "apenas vínculos celetistas ativos em 31 de dezembro, seus denominadores são "
 "comensuráveis com o numerador da CAT. Denominadores complementares do CNES-PF foram "
 "obtidos com o pacote [[i]]microdatasus[[/i]] (R) e sustentam razões exploratórias "
 "de densidade de comunicação. Células com menos de cinco registros foram agregadas.",

 # §8 - Resultados principais
 "Das 5.066 CATs vinculadas a empregadores de Campos dos Goytacazes entre 2018 e "
 "2025, 1.144 (22,6%) correspondem às profissões da saúde, 26 às multiprofissionais, "
 "184 (3,6%) a registros sem CBO válido e 3.712 às demais ocupações (427 em "
 "estabelecimentos de saúde). A distribuição é fortemente assimétrica (Tabela 5). A "
 "enfermagem concentra 84,4% dos registros, sendo 70,2% de técnicos e auxiliares e "
 "14,2% de enfermeiros. Seguem-se os técnicos de diagnóstico e laboratório (6,8%) e "
 "a fisioterapia (2,6%). A medicina responde por 1,0%. Predominam mulheres (85,7%), "
 "com idade mediana de 36 anos. Os acidentes típicos somam 81,9% e os de trajeto, "
 "17,1%. Ferimentos de punho e mãos lideram os diagnósticos (CID-10 S61, 25,1%; o "
 "dedo é a parte atingida em 43,9%), seguidos da exposição a doenças transmissíveis "
 "(Z20, 21,9%). Agentes infecciosos respondem por 26,9% dos causadores. Quase todos "
 "os empregadores pertencem à CNAE 86-87 (95,4%), com dominância hospitalar (8610, "
 "76,8%). O empregador emitiu 97,0% das CATs, com mediana de um dia. Houve um óbito "
 "e 1,0% de doenças relacionadas ao trabalho (Figuras 1 e 2).",

 # §9 - Análise de sensibilidade
 "A robustez dos achados foi testada em seis cenários. A exclusão do ano de 2025 "
 "(dados parciais até outubro) reduziu o universo principal para 1.011 registros, "
 "com a enfermagem mantendo 84,5% do total. A restrição aos meses de janeiro a "
 "outubro de todos os anos resultou em 994 registros, com 84,4% de enfermagem. A "
 "exclusão dos acidentes de trajeto, que podem refletir fatores externos ao ambiente "
 "laboral, manteve 948 registros e 85,1% de enfermagem. A restrição aos acidentes "
 "típicos resultou em 937 registros e 85,0% de enfermagem, com os técnicos e "
 "auxiliares respondendo por 70,5% e os enfermeiros por 14,4%. O cenário mais "
 "restritivo - acidentes típicos em estabelecimentos de saúde (CNAE 86-87) - "
 "totalizou 937 registros idênticos ao cenário de típicos, pois 100% dos acidentes "
 "típicos já ocorreram nesses estabelecimentos. Em todos os cenários, a participação "
 "da enfermagem variou entre 84,4% e 86,3% e a hierarquia das três principais "
 "categorias (técnicos de enfermagem, enfermeiros, diagnóstico/laboratório) "
 "permaneceu inalterada (Tabela 6).",

 # §10 - Discussão da estrutura das CATs
 "A concentração dos registros na base técnica da enfermagem expressa a divisão "
 "social e técnica do trabalho em saúde. A execução manual e corporal do cuidado "
 "(punção venosa, administração de medicamentos, manipulação de perfurocortantes, "
 "mobilização de pacientes) é delegada a categorias majoritariamente femininas, de "
 "menor renda e prestígio, submetidas a intensificação e sobrecarga (Cecilio e Lacaz, "
 "2012; Antunes, 2018). O setor saúde de Campos empregava 15.002 pessoas em 2024, com "
 "massa salarial anual de R$ 593,9 milhões e salário médio de 2,2 salários mínimos, "
 "tornando esse contingente economicamente relevante e vulnerável à oscilação das "
 "finanças públicas. A quase invisibilidade da medicina (12 CATs em oito anos, ante "
 "1.099 a 1.393 vínculos celetistas ativos de médicos na RAIS entre 2018 e 2025) não "
 "autoriza concluir menor exposição. Indica inserção predominante por vínculos "
 "estatutários, autônomos e de pessoa jurídica, não cobertos pela CAT, configurando "
 "desigualdade de proteção e de reconhecimento (Lemos, 2012). A coexistência dos dois "
 "regimes previdenciários materializa essa dualidade. O RPPS, com R$ 61,2 milhões em "
 "contribuições em 2024, cobre os estatutários e seus registros de afastamento não "
 "transitam pelo sistema da CAT. O INSS, com R$ 18,3 milhões no mesmo ano, cobre os "
 "celetistas e alimenta a base nacional de comunicações de acidente. Essa assimetria "
 "de visibilidade faz com que o perfil de acidentes capturado pela CAT represente "
 "apenas uma fração do funcionalismo da saúde municipal - justamente a fração mais "
 "precarizada e de menor remuneração.",

 # §11 - Discussão da evolução temporal
 "A média mensal de registros passou de 13,8 (julho de 2018 a fevereiro de 2020) "
 "para 14,5 no período crítico da covid-19 (março de 2020 a dezembro de 2021) e "
 "recuou para 11,9 no biênio seguinte (2022-2023), convergente com a sobrecarga "
 "pandêmica descrita para os trabalhadores da saúde (Vedovato [[i]]et al.[[/i]], "
 "2021). As oscilações de cobertura da fonte, contudo, impedem atribuição causal. "
 "A baixíssima frequência de comunicações de doença (1,0%) reforça o diagnóstico de "
 "subnotificação seletiva. O sistema registra a lesão aguda e visível, não o "
 "adoecimento lento produzido pela organização do trabalho. Os dados descrevem a "
 "estrutura interna das comunicações registradas, mas não permitem estimar incidência "
 "ou risco ocupacional. As razões exploratórias com denominadores do CNES-PF (13.839 "
 "profissionais em 2018, 18.382 em 2025) reforçam o gradiente. Nos anos de cobertura "
 "integral (2019 a 2021 e 2023) houve de 25,0 a 36,6 CATs por 1.000 técnicos e "
 "auxiliares de enfermagem ao ano, de 16,5 a 28,0 por 1.000 enfermeiros e 1,2 por "
 "1.000 médicos em 2019, com valores suprimidos nos demais anos por contagens "
 "inferiores a cinco.",

 # §12 - Implicações
 "Para a Vigilância em Saúde do Trabalhador e para a gestão municipal, os resultados "
 "indicam quatro prioridades. A primeira é proteger a base técnica da enfermagem, "
 "núcleo do cuidado e dos registros, com ênfase em perfurocortantes e exposição "
 "biológica. A segunda é enfrentar a subnotificação de doenças e a invisibilidade "
 "de estatutários, terceirizados e informais, articulando CAT, SINAN, RAIS, CNES-PF "
 "e os registros de afastamento do RPPS municipal (PREVICAMPOS), cujos dados não são "
 "consolidados em base nacional de acesso público. A integração desses sistemas "
 "permitiria dimensionar a carga real de acidentes e adoecimentos no funcionalismo "
 "da saúde, superando a assimetria de visibilidade entre regimes previdenciários. A "
 "terceira é qualificar o preenchimento dos registros, pois 3,6% não trazem código "
 "ocupacional válido. A quarta é planejar a rede assistencial reconhecendo que o "
 "financiamento da saúde oscila com os ciclos do petróleo (Martins, Hasenclever e "
 "Miranda, 2024) e que a proteção de quem cuida é condição do próprio cuidado. O "
 "IDHM de 0,716, a dependência de 71% das receitas de transferências e a convivência "
 "de dois regimes previdenciários com patamares desiguais de proteção reforçam a "
 "urgência de políticas que não estejam à mercê da volatilidade de uma única "
 "[[i]]commodity[[/i]].",

 # §13 - Limitações
 "A CAT capta comunicações, não a totalidade dos acidentes e adoecimentos. Cobre "
 "essencialmente o emprego formal celetista, excluindo informais, autônomos e "
 "estatutários. Não há denominadores plenamente compatíveis para cálculo de "
 "incidência. A cobertura da fonte é parcial em 2018 (competências desde julho), "
 "irregular em 2022, atípica de setembro a dezembro de 2024 e incompleta em 2025 "
 "(dados até outubro). Registros sem CBO válido podem subestimar as profissões da "
 "saúde entre 2021 e 2023. O desenho descritivo e documental não permite inferência "
 "causal. Os dados de acidentes e adoecimentos de estatutários, geridos pelo RPPS "
 "municipal, não estão disponíveis em base consolidada de acesso público, impedindo "
 "a comparação direta entre regimes.",
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
 ("Estimativa populacional", "519.259 hab.", "2025"),
 ("Densidade demográfica", "119,9 hab./km²", "2022"),
 ("População quilombola", "3.083 pessoas", "2022"),
 ("População indígena", "363 pessoas", "2022"),
 ("IDHM", "0,716", "2010"),
 ("PIB per capita", "R$ 88.831,26", "2023"),
 ("Salário médio (formal)", "2,1 salários mínimos", "2023"),
 ("Renda até ½ SM per capita", "37,7%", "2010"),
]

# Tabela 2 - Ciclos econômicos
T2 = [
 ("Ciclo", "Período", "Característica", "Impacto no mercado de trabalho"),
 ("Açucareiro", "Séc. XVIII a XX", "Monocultura, grande propriedade", "Trabalho escravizado, depois assalariado rural"),
 ("Petrolífero", "1970 a 2014", "Extrativismo, royalties", "Expansão do setor público empregador"),
 ("Estagnação", "2014 em diante", "Declínio dos repasses", "Desemprego, informalidade, pressão sobre o SUS"),
]

# Tabela 3 - Estrutura empresarial, finanças e regimes
T3 = [
 ("Indicador", "Valor", "Ano"),
 ("Empresas atuantes", "16.776", "2024"),
 ("Pessoal ocupado (assalariado)", "114.466 (93.366)", "2024"),
 ("Saúde: estab. / pessoal", "1.544 / 15.002", "2024"),
 ("Receitas brutas", "R$ 2,95 bilhões", "2024"),
 ("Transferências correntes", "71,0% das receitas", "2024"),
 ("Despesas empenhadas", "R$ 3,31 bilhões", "2024"),
 ("Contribuições RPPS (estatutários)", "R$ 61,2 milhões", "2024"),
 ("Contribuições INSS (celetistas)", "R$ 18,3 milhões", "2024"),
 ("Aporte déficit atuarial RPPS", "R$ 2,5 milhões", "2024"),
]

# Tabela 4 - Mortalidade
T4 = [
 ("Ano", "Óbitos", "Taxa/1.000", "1ª causa", "2ª causa"),
 ("2019", "4.299", "8,5", "Circulatórias", "Neoplasias"),
 ("2020", "4.831", "9,5", "Circulatórias", "Infecciosas"),
 ("2021", "5.635", "10,9", "Infecciosas", "Circulatórias"),
 ("2022", "4.608", "9,5", "Circulatórias", "Neoplasias"),
 ("2023", "4.199", "8,1", "Circulatórias", "Respiratórias"),
 ("2024", "4.346", "8,4", "Circulatórias", "Respiratórias"),
]

# Tabela 5 - Características das CATs
T5 = [
 ("Característica", "n (%)"),
 ("Enfermagem - técnicos e auxiliares", "803 (70,2)"),
 ("Enfermagem - enfermeiros", "163 (14,2)"),
 ("Diagnóstico/lab. - técnicos", "78 (6,8)"),
 ("Fisioterapia", "30 (2,6)"),
 ("Farmácia - técnicos", "20 (1,7)"),
 ("ACS e afins", "14 (1,2)"),
 ("Medicina", "12 (1,0)"),
 ("Demais (n<5 agregados)", "24 (2,1)"),
 ("Sexo feminino", "980 (85,7)"),
 ("Típico / trajeto / doença", "937 (81,9) / 196 (17,1) / 11 (1,0)"),
 ("Dedo", "502 (43,9)"),
 ("Agente biológico", "308 (26,9)"),
 ("CID-10 S61 / Z20", "287 (25,1) / 250 (21,9)"),
 ("CNAE 86-87 / 8610", "1.091 (95,4) / 879 (76,8)"),
 ("CAT pelo empregador", "1.110 (97,0)"),
]

# Tabela 6 - Análise de sensibilidade
T6 = [
 ("Cenário", "n", "Enfermagem (%)", "Medicina (n)", "Fisioterapia (n)"),
 ("Base completa 2018-2025 (referência)", "1.144", "84,4", "12", "30"),
 ("Excluindo 2025 (dados parciais)", "1.011", "84,5", "12", "30"),
 ("Somente jan-out (todos os anos)", "994", "84,4", "10", "26"),
 ("Excluindo acidentes de trajeto", "948", "85,1", "5", "27"),
 ("Somente acidentes típicos", "937", "85,0", "4", "28"),
 ("Típicos em CNAE 86-87", "937", "86,3", "4", "28"),
]

# ======================== MONTAGEM ============================================
for i, texto in enumerate(CORPO):
    par(texto, after=2)
    if i == 2:
        par("[[b]]Tabela 1.[[/b]] Campos dos Goytacazes (RJ): perfil sociodemográfico",
            indent=False, size=9.5, before=4, after=2)
        tabela(T1, "Fonte dos dados brutos: IBGE, Censo Demográfico 2022 e IBGE Cidades. SM = salário mínimo.")
    if i == 3:
        par("[[b]]Tabela 2.[[/b]] Campos dos Goytacazes (RJ): ciclos de formação econômica",
            indent=False, size=9.5, before=4, after=2)
        tabela(T2, "Fonte: elaborada pelo autor a partir de Silva e Hasenclever (2019), IBGE e literatura.")
    if i == 4:
        par("[[b]]Tabela 3.[[/b]] Campos dos Goytacazes (RJ): estrutura empresarial, finanças e regimes previdenciários",
            indent=False, size=9.5, before=4, after=2)
        tabela(T3, "Fontes dos dados brutos: IBGE, CEMPRE 2024; Siconfi/STN; Portal da Transparência de Campos, "
                   "despesas por natureza econômica, 2020-2024.")
    if i == 5:
        par("[[b]]Tabela 4.[[/b]] Campos dos Goytacazes (RJ): mortalidade geral de residentes, 2019-2024",
            indent=False, size=9.5, before=4, after=2)
        tabela(T4, "Fonte dos dados brutos: SIM/DATASUS, processados com microdatasus (R). "
                   "Denominadores populacionais do IBGE.")
    if i == 7:
        par("[[b]]Tabela 5.[[/b]] Características das CATs das profissões da saúde, Campos dos Goytacazes (RJ), "
            "2018-2025 (n = 1.144)", indent=False, size=9.5, before=4, after=2)
        tabela(T5, "Fonte dos dados brutos: INSS, CAT, Portal de Dados Abertos. Idade mediana de 36 anos. "
                   "Sexo ignorado em 4 registros. Um óbito. Percentuais sobre o universo principal (n = 1.144).")
        figura("saidas/figuras/F1_cat_ano_categorias.png",
               "[[b]]Figura 1.[[/b]] CATs de profissões da saúde (universo principal, n = 1.144), Campos dos "
               "Goytacazes (RJ), por ano do acidente e categoria profissional, 2018-2025. *Cobertura parcial "
               "ou irregular da fonte.")
        figura("saidas/figuras/F2_serie_mensal_saude.png",
               "[[b]]Figura 2.[[/b]] Distribuição mensal das CATs de profissões da saúde (universo principal, "
               "n = 1.144), Campos dos Goytacazes (RJ), janeiro de 2018 a dezembro de 2025. Destaque para "
               "o período crítico da covid-19 e médias mensais por período. Ver notas da Figura 1.")
    if i == 8:
        par("[[b]]Tabela 6.[[/b]] Análise de sensibilidade das CATs do universo principal, Campos dos Goytacazes (RJ), "
            "2018-2025", indent=False, size=9.5, before=4, after=2)
        tabela(T6, "Fonte dos dados brutos: INSS, CAT. Cenários testados para verificar a estabilidade dos achados "
                   "principais. Em todos os cenários a hierarquia das categorias manteve-se inalterada.")

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
conteudo += " ".join(v for linha in T1 + T2 + T3 + T4 + T5 + T6 for v in linha)
for proibido, nome in ((TRAVESSAO, "travessão"), (MEIA_RISCA, "meia-risca")):
    if proibido in conteudo:
        raise SystemExit(f"PROIBIDO: {nome} encontrado.")

os.makedirs("documentos", exist_ok=True)
d.save("documentos/artigo.docx")

soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
if os.path.exists(soffice):
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", "documentos",
                    "documentos/artigo.docx"], capture_output=True, timeout=300)
    from pypdf import PdfReader
    npag = len(PdfReader("documentos/artigo.pdf").pages)
    print(f"artigo.docx gerado (sem travessao) com {npag} pagina(s) no PDF de verificacao.")
    if npag > 10:
        raise SystemExit(f"LIMITE EXCEDIDO: artigo com {npag} paginas (maximo 10).")
else:
    print("AVISO: LibreOffice ausente; numero de paginas NAO verificado.")
