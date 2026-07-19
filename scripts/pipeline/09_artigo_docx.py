# -*- coding: utf-8 -*-
"""
09_artigo_docx.py - Gera documentos/artigo.docx (A4, margens 2,5 cm, Times New Roman 11,
espaçamento 1,5, recuo 1,25 cm, máximo 10 páginas).

REGRAS:
- PROIBIDO travessão, meia-risca, dois-pontos no corpo do texto
- Sem resumo. Sem projeções.
- Português correto com acentos. Conectivos científicos.
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
par("[[b]]Trabalho, saúde e profissão em Campos dos Goytacazes (RJ)[[/b]]",
    indent=False, center=True, size=12, after=6)

# ======================== CORPO ================================================
CORPO = [
 # §1 - INTRODUÇÃO
 "Este ensaio sustenta que a estrutura de vínculos previdenciários do município de "
 "Campos dos Goytacazes, conformada por sua economia política dependente do petróleo, "
 "produz um regime de visibilidade seletiva dos acidentes de trabalho no setor saúde. "
 "Nesse regime, categorias majoritariamente femininas, de menor remuneração e vínculo "
 "celetista tornam-se hipervisíveis na Comunicação de Acidente de Trabalho (CAT), "
 "ao passo que categorias de maior remuneração e vínculo estatutário permanecem "
 "institucionalmente invisíveis. Argumenta-se que essa assimetria constitui a "
 "manifestação local da distância entre o campo institucional da Saúde do Trabalhador "
 "e a questão estrutural da saúde dos trabalhadores, conforme a distinção proposta "
 "por Souza, Melo e Vasconcellos (2017). O campo opera dentro dos limites normativos "
 "postos, e a CAT é seu instrumento por excelência. A questão, contudo, é mais ampla. "
 "Inclui os acidentes e adoecimentos que o sistema não captura e cuja distribuição "
 "obedece a determinações de classe, gênero e raça que ultrapassam as fronteiras do "
 "campo. França (2014), ao correlacionar o Modelo Operário Italiano com as categorias "
 "gramscianas, demonstra que o saber operário e a participação dos trabalhadores são "
 "fundamentais para uma vigilância que supere os limites do registro administrativo. "
 "O presente ensaio mobiliza esse arcabouço conceitual para construir um diagnóstico "
 "estrutural da saúde do trabalhador no setor saúde de Campos, articulando oito bases "
 "de dados secundárias independentes. O território onde esse regime opera é precisamente "
 "o que se descreve a seguir.\n\n"
 "O município de Campos dos Goytacazes, maior do estado do Rio de Janeiro em extensão "
 "territorial, com 4.032,5 km², contava com 483.540 habitantes no Censo Demográfico de "
 "2022 do IBGE e estimativa de 519.259 para 2025. Sua população se declara branca "
 "(42,1%), parda (40,1%) e preta (17,7%), com 3.083 quilombolas e 363 indígenas "
 "recenseados, segundo a tabela SIDRA 4714 do IBGE. O Índice de Desenvolvimento Humano "
 "Municipal era de 0,716 em 2010, abaixo da média estadual de 0,761, e 37,7% da "
 "população vivia com até meio salário mínimo per capita. O Produto Interno Bruto per "
 "capita de 2023 foi de R$ 88.831,26, segundo a tabela SIDRA 5938 do IBGE. Nesse "
 "contexto de riqueza concentrada e indicadores sociais frágeis, este estudo investiga "
 "os acidentes de trabalho entre os profissionais da saúde que operam a rede municipal "
 "de atendimento.",

 # §2 - IPS E MORTALIDADE
 "O Índice de Progresso Social de Campos, calculado pelo IPS Brasil para 2024, 2025 e "
 "2026 a partir de indicadores sociais e ambientais desagregados por município, mostra "
 "trajetória ambivalente, conforme a Tabela 1. O índice global passou de 62,37, em 2024, "
 "para 62,68, em 2026, com variação de 0,31 ponto. Saúde e Bem-estar avançou 1,47 ponto, "
 "de 57,43 para 58,90, e Acesso ao Conhecimento Básico avançou 3,41 pontos. Em "
 "contrapartida, Segurança Pessoal recuou 3,58 pontos, de 56,35 para 52,77, Inclusão "
 "Social caiu 2,70 pontos e as Hospitalizações por Condições Sensíveis à Atenção "
 "Primária aumentaram 45%, de 610 para 883 por 100 mil habitantes. Nesse sentido, o "
 "município avança nas dimensões de infraestrutura de saúde e conhecimento, mas recua "
 "em segurança e inclusão, configurando um paradoxo que interpela diretamente as "
 "condições de trabalho de quem opera os serviços cuja qualidade melhora."
 "\n\n"
 "O perfil de mortalidade do município, obtido do SIM/DATASUS e processado com o pacote "
 "[[i]]microdatasus[[/i]] em R, registrou entre 4.199 e 5.635 óbitos anuais de "
 "residentes de 2019 a 2024, com taxa bruta variando de 8,1 a 10,9 por 1.000 "
 "habitantes (Tabela 2). Em 2021, auge da pandemia, as doenças infecciosas deslocaram-se "
 "para a primeira posição, com 1.548 óbitos (27,5%), ultrapassando as circulatórias, que "
 "retomaram a liderança a partir de 2022. As causas externas mantiveram-se entre as "
 "cinco primeiras em todo o período. Esse perfil funciona como indicador composto de "
 "desenvolvimento social e de pressão assistencial sobre o sistema de saúde. A taxa de "
 "homicídios, registrada pelo IPS, variou entre 24,6 e 27,9 por 100 mil habitantes no "
 "triênio 2024-2026, valores que pressionam diretamente os serviços de emergência.",

 # §3 - ESTRUTURA ECONÔMICA E REGIMES PREVIDENCIÁRIOS
 "A formação econômica de Campos organiza-se em três ciclos que moldaram o mercado de "
 "trabalho em saúde, conforme demonstram Silva e Hasenclever (2019). O ciclo açucareiro, "
 "que se estendeu do século XVIII ao XX, entrou em colapso a partir dos anos 1980 com o "
 "fechamento de usinas, produzindo desemprego em massa e reconfigurando a estrutura "
 "ocupacional do município. O ciclo petrolífero, de 1970 a 2014, impulsionado pela "
 "descoberta da Bacia de Campos, gerou receitas expressivas de [[i]]royalties[[/i]] e "
 "participações especiais, nos termos da Lei nº 9.478/1997, que expandiram o setor público municipal. O terceiro ciclo, em "
 "curso desde 2014, caracteriza-se pela estagnação da atividade petrolífera e pelo "
 "declínio dos repasses. A estrutura empresarial do município, captada pelo Cadastro "
 "Central de Empresas do IBGE, o CEMPRE 2024, registra 16.776 empresas atuantes, "
 "114.466 pessoas ocupadas, das quais 93.366 assalariadas, e salário médio mensal de "
 "2,2 salários mínimos. O setor de saúde humana e serviços sociais respondia por 1.544 "
 "estabelecimentos e 15.002 postos de trabalho, conforme o CEMPRE 2024. O PIB municipal, "
 "a preços correntes, oscilou de R$ 58,4 bilhões em 2013 para R$ 23,9 bilhões em 2020 e "
 "R$ 43,0 bilhões em 2023, de acordo com a tabela SIDRA 5938 do IBGE, acompanhando a "
 "volatilidade do petróleo."
 "\n\n"
 "As finanças públicas municipais evidenciam dependência estrutural de transferências "
 "intergovernamentais. Em 2024, as receitas brutas somaram R$ 2,95 bilhões, das quais "
 "71,0% provieram de transferências correntes, segundo o Siconfi da Secretaria do "
 "Tesouro Nacional. As despesas por natureza econômica, obtidas do Portal da "
 "Transparência da Prefeitura de Campos para o período de 2020 a 2025, na rubrica "
 "Despesas por Desdobro, revelam a coexistência de dois regimes previdenciários no "
 "funcionalismo municipal. Haja vista a relevância desse achado para o estudo, "
 "detalham-se os montantes. O Regime Próprio de Previdência Social, o RPPS, cobre os "
 "servidores estatutários e suas contribuições patronais somaram R$ 61,2 milhões em "
 "2024, acrescidas de R$ 2,5 milhões de aporte para cobertura do déficit atuarial. Em "
 "2025, as contribuições ao RPPS para pessoal ativo alcançaram R$ 74,7 milhões, "
 "conforme a rubrica 31911308 do Portal da Transparência. O Regime Geral de Previdência "
 "Social, o INSS, cobre os trabalhadores celetistas, com contribuições patronais de "
 "R$ 18,3 milhões em 2024 e R$ 4,8 milhões em 2025 na principal rubrica do Regime Geral, "
 "segundo os mesmos registros do Portal da Transparência de Campos. A razão entre as "
 "contribuições, RPPS sobre INSS, foi de 3,3 em 2024 e ampliou-se para aproximadamente "
 "15,5 em 2025, indicando que a predominância orçamentária do vínculo estatutário se "
 "acentuou no último exercício. A Comunicação de Acidente de Trabalho, a CAT, instituída "
 "pela Lei nº 8.213 de 1991, é instrumento exclusivo do INSS. Os acidentes e adoecimentos "
 "dos servidores estatutários, vinculados ao RPPS e geridos pelo PREVICAMPOS, não são "
 "capturados por essa fonte. Essa dualidade de regimes produz uma assimetria fundamental "
 "de visibilidade previdenciária que estrutura os achados deste ensaio, conforme a "
 "Tabela 3.",

 # §4 - MÉTODOS
 "Este ensaio integra uma agenda mais ampla de investigação sobre a Saúde do "
 "Trabalhador em Campos dos Goytacazes. Seu propósito é construir o diagnóstico "
 "territorial e institucional necessário para estudos posteriores sobre "
 "processos de trabalho, adoecimento e vigilância. Trata-se de uma análise "
 "exploratória do território apoiada na triangulação de bases secundárias "
 "independentes, cujo objetivo é caracterizar a configuração contemporânea "
 "da saúde do trabalhador no setor saúde do município e identificar elementos "
 "estruturantes para investigações subsequentes. A base empírica principal "
 "foi reconstruída dos dados abertos da CAT do INSS, disponíveis no Portal "
 "de Dados Abertos do governo federal. Foram processados 58 arquivos, de "
 "julho de 2018 a outubro de 2025, totalizando 3.902.905 registros, com "
 "importação posicional e remoção de 938 duplicatas (401 hashes SHA-256). "
 "O recorte municipal utilizou código do empregador 330100 e UF Rio de "
 "Janeiro. A classificação ocupacional baseou-se na CBO 2002, com dicionário "
 "auditado de 458 códigos."

 "\n\n"
 "O denominador primário de força de trabalho proveio da RAIS, a Relação Anual de "
 "Informações Sociais, disponível no FTP do Ministério do Trabalho e Emprego. Como a "
 "RAIS captura vínculos celetistas ativos em 31 de dezembro de cada ano e a CAT cobre "
 "exclusivamente celetistas, numerador e denominador são comensuráveis. O denominador "
 "secundário proveio do CNES-PF, o Cadastro Nacional de Estabelecimentos de Saúde, "
 "obtido com o pacote [[i]]microdatasus[[/i]] em R para a competência de dezembro de "
 "cada ano, acessado via FTP do DATASUS. O CNES-PF, por incluir vínculos estatutários, "
 "autônomos e de pessoa jurídica, não é comensurável com a CAT, sendo utilizado como "
 "ferramenta de triangulação para estimar a fração de vínculos não capturados. Células "
 "com menos de cinco registros foram suprimidas."
 "\n\n"
"Para a caracterização do território, três abordagens complementares foram "
 "empregadas. A primeira compreendeu a descrição do perfil das CATs das "
 "profissões da saúde, com teste de sensibilidade em seis cenários para "
 "verificar a estabilidade dos achados. A segunda consistiu na análise da "
 "série temporal mensal de CATs (janeiro de 2018 a outubro de 2025), com "
 "decomposição clássica, Mann-Kendall, Dickey-Fuller e suavização LOESS com "
 "intervalo de confiança [[i]]bootstrap[[/i]] de 200 reamostragens. A terceira "
 "compreendeu a identificação de padrões de associação entre ocupação, agente "
 "causador e diagnóstico, utilizando o algoritmo Apriori (métricas de suporte, "
 "confiança e [[i]]lift[[/i]]), grafos bipartidos e teste qui-quadrado com "
 "V de Cramér. Essas abordagens identificam regularidades que contribuam "
 "para a caracterização do regime de visibilidade previdenciária. "
 "Adicionalmente, 46 arquivos do SINAN/DATASUS (126,5 MB, nove agravos "
 "relacionados ao trabalho, 2018-2022, FTP do DATASUS) foram obtidos para "
 "cotejo futuro entre notificação compulsória e comunicação de acidente.\n\n"
 # §5 - RESULTADOS DESCRITIVOS
 "Das 5.066 CATs vinculadas a empregadores de Campos dos Goytacazes entre 2018 e 2025, "
 "1.144, equivalentes a 22,6%, correspondem às profissões da saúde, 26 às "
 "multiprofissionais, 184, ou 3,6%, a registros sem CBO válido e 3.712 às demais "
 "ocupações, das quais 427 em estabelecimentos de saúde. A distribuição é fortemente "
 "assimétrica, conforme a Tabela 4. A enfermagem concentra 84,4% dos registros, sendo "
 "70,2% de técnicos e auxiliares e 14,2% de enfermeiros. Seguem-se os técnicos de "
 "diagnóstico e laboratório, com 6,8%, e a fisioterapia, com 2,6%. A medicina responde "
 "por 1,0%, o que representa 12 CATs em oito anos. Predominam mulheres, com 85,7%, e a "
 "idade mediana é de 36 anos. Os acidentes típicos somam 81,9% e os de trajeto, 17,1%. "
 "Ferimentos de punho e mãos lideram os diagnósticos, CID-10 S61, com 25,1%, sendo o "
 "dedo a parte atingida em 43,9% dos casos, seguidos da exposição a doenças "
 "transmissíveis, código Z20, com 21,9%. Agentes infecciosos respondem por 26,9% dos "
 "causadores. Quase todos os empregadores pertencem à CNAE 86-87, com 95,4%, e há "
 "dominância hospitalar, CNAE 8610, com 76,8%. O empregador emitiu 97,0% das CATs, "
 "com mediana de um dia entre o acidente e a emissão. Houve um óbito e 1,0% de "
 "doenças relacionadas ao trabalho."
 "\n\n"
 "A análise de sensibilidade em seis cenários confirmou a estabilidade dos achados, "
 "conforme a Tabela 5. Em todos os cenários, a participação da enfermagem variou entre "
 "84,4% e 86,3% e a hierarquia das três principais categorias, a saber, técnicos de "
 "enfermagem, enfermeiros e profissionais de diagnóstico e laboratório, permaneceu "
 "inalterada. As Figuras 1 e 2 ilustram esses resultados.",

 # §6 - SÉRIES TEMPORAIS
 "A série mensal de CATs das profissões da saúde, abrangendo 94 meses de janeiro de "
 "2018 a outubro de 2025, totalizou 1.144 registros, com média geral de 12,2 CATs por "
 "mês e desvio padrão de 6,9. A decomposição clássica evidenciou componente sazonal "
 "discreto e tendência estável, com elevação durante o período pandêmico. O teste de "
 "Mann-Kendall não detectou tendência monotônica significativa na série completa, com "
 "tau de Kendall igual a 0,06 e p igual a 0,41. No entanto, a análise por subperíodo "
 "revelou tendência de aumento significativa durante a pandemia, mais precisamente de "
 "março de 2020 a dezembro de 2021, com p igual a 0,002 e [[i]]slope[[/i]] de 0,50 "
 "CATs por mês, achado compatível com a intensificação da exposição ocupacional no "
 "período crítico da covid-19, conforme descrito por Vedovato [[i]]et al.[[/i]] (2021). "
 "Nos períodos pré-pandemia, de janeiro de 2018 a fevereiro de 2020, e pós-pandemia, de "
 "janeiro de 2022 a outubro de 2025, a tendência não foi significativa, com p igual a "
 "0,21 e p igual a 0,40, respectivamente."
 "\n\n"
 "O teste de Dickey-Fuller aumentado rejeitou a hipótese de raiz unitária, com ADF igual "
 "a -5,80 e p inferior a 0,001, indicando que a série é estacionária. A média mensal de "
 "CATs foi de 13,8 no período pré-pandemia, de julho de 2018 a fevereiro de 2020, 14,5 "
 "no período crítico da covid-19 e 10,9 no biênio pós-pandemia, de 2022 a 2023. O teste "
 "t de Welch detectou diferença significativa apenas entre os períodos crítico e "
 "pós-pandemia, com t igual a 2,04 e p igual a 0,048. O coeficiente de variação "
 "aumentou de 37,5% no pré-pandemia para 63,3% no pós-pandemia, indicando maior "
 "irregularidade das notificações nos anos recentes, possivelmente associada às "
 "oscilações de cobertura da fonte. A Tabela 6 e as Figuras 3 e 4 apresentam esses "
 "resultados.",

 # §7 - REDES DE ASSOCIAÇÃO
 "A mineração de regras de associação revelou duas cadeias de acidentes estruturalmente "
 "distintas, conforme a Tabela 7 e a Figura 5. A primeira associa ferramenta manual, "
 "enfermagem de nível técnico, ferimento de punho e mão, código S61 da CID-10, e lesão "
 "imediata, com [[i]]lift[[/i]] de 6,29 e confiança de 85% na direção reversa. A "
 "segunda associa agente biológico, enfermagem de nível técnico e exposição a doenças "
 "transmissíveis, código Z20 da CID-10. O teste qui-quadrado de independência entre "
 "ocupação e grupo CID-10 foi significativo, com qui-quadrado igual a 352,6, 268 graus "
 "de liberdade, p inferior a 0,001 e V de Cramér igual a 0,28, confirmando que o perfil "
 "diagnóstico não é homogêneo entre as categorias profissionais. A enfermagem de nível "
 "técnico apresentou prevalência três vezes maior de causas externas, código Y da "
 "CID-10, com razão de prevalência de 3,02, e de traumatismos de punho e mão, códigos "
 "S60 a S69, com razão de prevalência de 2,97, em comparação com as demais categorias. "
 "A exposição a doenças transmissíveis, código Z20, também foi mais prevalente na "
 "enfermagem técnica, com razão de prevalência de 1,37. A análise de cadeias completas, "
 "envolvendo ocupação, agente, CID e tipo de acidente, confirmou que as cinco combinações "
 "mais frequentes envolvem a enfermagem técnica. A principal delas corresponde a agente "
 "biológico associado a exposição a doenças transmissíveis em acidente típico, com 116 "
 "ocorrências, seguida por agente biológico com ferimento de mão em acidente típico, "
 "com 84 ocorrências, e ferramenta manual com ferimento de mão em acidente típico, com "
 "80 ocorrências.",

 # §8 - SINAN
 "Os dados do SINAN para Campos (2018-2022), obtidos do FTP do DATASUS, abrangem "
 "nove agravos relacionados ao trabalho em 46 arquivos nacionais (126,5 MB). A "
 "comparação entre as notificações do SINAN e as comunicações da CAT para o mesmo "
 "município permite antever a complementaridade entre os sistemas. Enquanto a CAT "
 "captura majoritariamente acidentes entre celetistas, o SINAN registra agravos de "
 "notificação compulsória independentemente do vínculo, oferecendo uma janela para "
 "adoecimentos crônicos relacionados ao trabalho que a CAT não alcança.",

 # §9 - DISCUSSÃO
 "Os achados convergem para a demonstração de que o perfil de acidentes capturado "
 "pela CAT constitui, antes de tudo, um perfil do regime de visibilidade previdenciária "
 "do município. A concentração de 84,4% das CATs na enfermagem de nível técnico expressa, "
 "simultaneamente, a exposição diferencial ao risco determinada por um processo de "
 "trabalho que concentra a execução manual do cuidado em categorias subordinadas na "
 "hierarquia ocupacional, e a captura diferencial pelo sistema de informação "
 "determinada pelo regime previdenciário. Duas cadeias predominantes de risco "
 "prevenível emergem dessa concentração. A cadeia perfurocortante, que articula "
 "ferramenta manual ao código S61, e a cadeia biológica, que articula agente infeccioso "
 "ao código Z20, dependem de dispositivos de segurança e de disponibilidade contínua de "
 "equipamentos de proteção individual. A razão de prevalência elevada de causas externas, "
 "de 3,02, na enfermagem técnica é consistente com a execução manual e corporal do "
 "cuidado, que envolve punção venosa, administração de medicamentos e manipulação de "
 "perfurocortantes."
 "\n\n"
 "A concentração das CATs na "
 "enfermagem e a quase ausência da medicina, com apenas 1,0%, refletem a estrutura "
 "de vínculos previdenciários do município. A razão RPPS sobre INSS, que passou de 3,3 em 2024 "
 "para aproximadamente 15,5 em 2025, conforme os dados do Portal da Transparência de "
 "Campos, materializa essa assimetria e indica seu agravamento recente. As densidades "
 "de comunicação calculadas com denominador RAIS, que é comensurável com a CAT por "
 "ambos cobrirem celetistas, situaram-se entre 30,3 e 43,9 CATs por 1.000 vínculos "
 "ativos de técnicos de enfermagem, conforme a RAIS disponível no FTP do Ministério "
 "do Trabalho, e em apenas 3,7 por 1.000 para a medicina em 2019, único ano com "
 "numerador igual ou superior a cinco nessa categoria. As densidades com denominador "
 "CNES, que não é comensurável por incluir todos os vínculos, foram sistematicamente "
 "menores, mas a razão entre as densidades RAIS e CNES quantifica a fração de acidentes "
 "ocultos pelo desenho institucional da CAT."
 "\n\n"
 "Conforme exposto na abertura deste ensaio, Souza, Melo e Vasconcellos (2017) "
 "oferecem uma distinção entre campo e questão que ilumina esses achados. A CAT "
 "constitui um instrumento do campo, pois captura o que o desenho "
 "institucional permite ver. A questão, contudo, é mais ampla, uma vez que os "
 "acidentes e adoecimentos dos estatutários, autônomos, informais e terceirizados "
 "existem independentemente de sua captura pelo sistema. A dualidade de regimes "
 "previdenciários em Campos, com uma razão RPPS sobre INSS que se ampliou de 3,3 "
 "para 15,5 entre 2024 e 2025, é a manifestação local dessa distância entre o campo "
 "e a questão."
 "\n\n"
 "O pensamento de Antonio Gramsci, particularmente sua concepção do trabalho como "
 "princípio educativo e dos trabalhadores como produtores de conhecimento, oferece "
 "fundamentos para uma vigilância que articule processo de trabalho, determinação "
 "social da saúde e participação dos trabalhadores. França (2014), ao correlacionar "
 "o Modelo Operário Italiano com as categorias gramscianas, demonstra que o saber "
 "operário e a socialização do conhecimento foram fundamentais na construção de uma "
 "metodologia de ação contra a nocividade no trabalho protagonizada pelo próprio "
 "trabalhador. A saúde, nessa perspectiva, é algo a ser construído com participação "
 "direta. A vigilância baseada exclusivamente "
 "nos registros da CAT opera na institucionalidade consolidada, ao passo que a "
 "vigilância que incorpora a participação ativa dos trabalhadores na identificação "
 "dos riscos e na proposição de soluções avança na direção contra-hegemônica "
 "demonstrada pela experiência do Modelo Operário Italiano.",

 # §10 - LIMITAÇÕES
 "A CAT capta comunicações, não a totalidade dos acidentes e adoecimentos, e cobre "
 "essencialmente o emprego formal celetista, excluindo informais, autônomos e "
 "estatutários. A cobertura da fonte é parcial em 2018, com competências apenas desde "
 "julho, irregular em 2022, atípica de setembro a dezembro de 2024 e incompleta em "
 "2025, com dados até outubro, o que introduz ruído nas séries temporais. Registros "
 "sem CBO válido, que somam 3,6% do total, podem subestimar as profissões da saúde "
 "entre 2021 e 2023. O desenho exploratório do ensaio não comporta inferência causal. "
 "O CNES-PF como denominador não é comensurável com o numerador da CAT, limitação "
 "enfrentada com a utilização da RAIS como denominador primário comensurável e a "
 "transformação do CNES em ferramenta de triangulação. Ademais, a indisponibilidade "
 "dos registros de afastamento do RPPS municipal, geridos pelo PREVICAMPOS, em base "
 "pública consolidada impede a comparação direta entre os dois regimes previdenciários "
 "para as mesmas categorias profissionais. Por fim, o ensaio não contempla análise "
 "direta do processo de trabalho, lacuna que demanda estudos qualitativos "
 "complementares com participação dos trabalhadores, nos moldes do Modelo Operário "
 "Italiano (França, 2014).",

 # §11 - IMPLICAÇÕES
 "Para a Vigilância em Saúde do Trabalhador e para a gestão municipal, os resultados "
 "indicam quatro prioridades. A primeira consiste em proteger a base técnica da "
 "enfermagem, que concentra 84,4% dos registros, com dispositivos de segurança para "
 "perfurocortantes e disponibilidade contínua de equipamentos de proteção individual. "
 "A segunda reside na integração dos registros de afastamento do RPPS, geridos pelo "
 "PREVICAMPOS, à base da CAT, superando a assimetria de visibilidade que impede "
 "dimensionar a carga real de acidentes. A terceira concerne à incorporação da análise "
 "de séries temporais e de redes de associação à rotina da vigilância, haja vista que "
 "cadeias específicas de acidentes permitem intervenções mais efetivas que abordagens "
 "genéricas. A quarta diz respeito ao planejamento da força de trabalho, reconhecendo "
 "que a dependência fiscal do município, com 71% de transferências correntes segundo "
 "o Siconfi, torna o emprego em saúde vulnerável à volatilidade dos [[i]]royalties[[/i]] "
 "do petróleo (Martins, Hasenclever e Miranda, 2024).",
]

# ======================== TABELAS E FIGURAS ====================================
def tabela(dados_tab, fonte_txt):
    t = d.add_table(rows=0, cols=len(dados_tab[0])); t.style = "Table Grid"
    for i, row in enumerate(dados_tab):
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].text = ""
            _runs(cells[j].paragraphs[0], v, 7.5)
            for r_ in cells[j].paragraphs[0].runs:
                r_.bold = r_.bold or (i == 0)
    par(fonte_txt, indent=False, size=8, after=4)

def figura(path, caption):
    pf = d.add_paragraph(); pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.paragraph_format.space_before = Pt(3)
    pf.add_run().add_picture(path, width=Cm(10.5))
    par(caption, indent=False, size=8, after=3)

# Tabela 1 - IPS
T1 = [
 ("Indicador IPS", "2024", "2025", "2026", "Variação", "Fonte"),
 ("IPS Global", "62,37", "62,19", "62,68", "+0,31", "IPS Brasil"),
 ("Saúde e Bem-estar", "57,43", "58,59", "58,90", "+1,47", "IPS Brasil"),
 ("Acesso ao Conhecimento", "66,07", "66,17", "69,48", "+3,41", "IPS Brasil"),
 ("Direitos Individuais", "46,39", "44,62", "51,92", "+5,53", "IPS Brasil"),
 ("Segurança Pessoal", "56,35", "54,53", "52,77", "-3,58", "IPS Brasil"),
 ("Inclusão Social", "50,25", "50,67", "47,55", "-2,70", "IPS Brasil"),
 ("Hospitalizações CSAP", "610", "883", "883", "+273", "IPS Brasil"),
 ("Homicídios (100 mil)", "24,6", "27,9", "25,3", "+0,7", "IPS Brasil"),
]

# Tabela 2 - Mortalidade
T2 = [
 ("Ano", "Óbitos", "Taxa/1.000", "1ª causa", "2ª causa", "Fonte"),
 ("2019", "4.299", "8,5", "Circulatórias", "Neoplasias", "SIM/DATASUS"),
 ("2020", "4.831", "9,5", "Circulatórias", "Infecciosas", "SIM/DATASUS"),
 ("2021", "5.635", "10,9", "Infecciosas", "Circulatórias", "SIM/DATASUS"),
 ("2022", "4.608", "9,5", "Circulatórias", "Neoplasias", "SIM/DATASUS"),
 ("2023", "4.199", "8,1", "Circulatórias", "Respiratórias", "SIM/DATASUS"),
 ("2024", "4.346", "8,4", "Circulatórias", "Respiratórias", "SIM/DATASUS"),
]

# Tabela 3 - Estrutura e regimes
T3 = [
 ("Indicador", "2024", "2025", "Fonte"),
 ("Receitas brutas", "R$ 2,95 bi", "-", "Siconfi/STN"),
 ("Transferências correntes", "71,0%", "-", "Siconfi/STN"),
 ("Pessoal ocupado na saúde", "15.002", "-", "IBGE, CEMPRE 2024"),
 ("Contribuições RPPS", "R$ 63,7 mi", "R$ 74,7 mi", "Portal Transparência Campos"),
 ("Contribuições INSS", "R$ 18,3 mi", "R$ 4,8 mi", "Portal Transparência Campos"),
 ("Razão RPPS/INSS", "3,3", "~15,5", "Portal Transparência Campos"),
]

# Tabela 4 - CATs
T4 = [
 ("Característica", "n (%)", "Fonte"),
 ("Enfermagem - técnicos e auxiliares", "803 (70,2)", "CAT/INSS"),
 ("Enfermagem - enfermeiros", "163 (14,2)", "CAT/INSS"),
 ("Diagnóstico/lab. - técnicos", "78 (6,8)", "CAT/INSS"),
 ("Fisioterapia", "30 (2,6)", "CAT/INSS"),
 ("Farmácia - técnicos", "20 (1,7)", "CAT/INSS"),
 ("ACS e afins", "14 (1,2)", "CAT/INSS"),
 ("Medicina", "12 (1,0)", "CAT/INSS"),
 ("Demais (n<5 agregados)", "24 (2,1)", "CAT/INSS"),
 ("Sexo feminino", "980 (85,7)", "CAT/INSS"),
 ("Típico / trajeto / doença", "937 / 196 / 11", "CAT/INSS"),
 ("Dedo", "502 (43,9)", "CAT/INSS"),
 ("Agente biológico", "308 (26,9)", "CAT/INSS"),
 ("CID-10 S61 / Z20", "287 / 250", "CAT/INSS"),
 ("CNAE 86-87 / 8610", "1.091 / 879", "CAT/INSS"),
 ("CAT pelo empregador", "1.110 (97,0)", "CAT/INSS"),
]

# Tabela 5 - Sensibilidade
T5 = [
 ("Cenário", "n", "Enfermagem (%)", "Fonte"),
 ("Base completa 2018-2025", "1.144", "84,4", "CAT/INSS"),
 ("Excluindo 2025", "1.011", "84,5", "CAT/INSS"),
 ("Somente janeiro a outubro", "994", "84,4", "CAT/INSS"),
 ("Excluindo trajeto", "948", "85,1", "CAT/INSS"),
 ("Somente típicos", "937", "85,0", "CAT/INSS"),
 ("Típicos em CNAE 86-87", "937", "86,3", "CAT/INSS"),
]

# Tabela 6 - Séries temporais
T6 = [
 ("Teste", "Estatística", "p-valor", "Interpretação"),
 ("Mann-Kendall (série completa)", "tau = 0,06", "0,4116", "Sem tendência global"),
 ("Mann-Kendall (pandemia)", "slope = 0,50/mês", "0,0020", "Aumento na pandemia"),
 ("Dickey-Fuller Aumentado", "ADF = -5,80", "< 0,001", "Série estacionária"),
 ("t-test covid vs pós-pandemia", "t = 2,04", "0,0480", "Diferença significativa"),
 ("CV pré-pandemia / pós", "37,5% / 63,3%", "-", "Maior irregularidade recente"),
]

# Tabela 7 - Regras de associação
T7 = [
 ("Regra de associação", "Confiança", "Lift", "n", "Fonte"),
 ("Ferramenta manual → Enf. técnica + S61", "0,36", "6,29", "55", "CAT/INSS"),
 ("S61 + Lesão imediata → Ferramenta manual", "0,81", "6,00", "63", "CAT/INSS"),
 ("Ag. biológico + Enf. técnica → Z20", "0,82", "2,45", "116", "CAT/INSS"),
 ("Enf. técnica + Ag. biológico → Típico", "0,97", "1,18", "188", "CAT/INSS"),
 ("Ferramenta manual + Típico → S61", "0,93", "3,63", "94", "CAT/INSS"),
]

# ======================== MONTAGEM ============================================
for i, texto in enumerate(CORPO):
    par(texto, indent=True, after=2)
    if i == 1:
        par("[[b]]Tabela 1.[[/b]] Evolução do IPS de Campos dos Goytacazes (RJ), 2024-2026",
            indent=False, size=9.5, before=4, after=2)
        tabela(T1, "Fonte dos dados brutos: IPS Brasil 2024, 2025 e 2026 (https://ipsbrasil.org.br). "
                   "CSAP = Condições Sensíveis à Atenção Primária, por 100 mil habitantes.")
        par("[[b]]Tabela 2.[[/b]] Mortalidade geral de residentes, Campos dos Goytacazes (RJ), 2019-2024",
            indent=False, size=9.5, before=2, after=2)
        tabela(T2, "Fonte dos dados brutos: SIM/DATASUS, processados com microdatasus (R). "
                   "Denominadores populacionais do IBGE, Estimativas Populacionais, SIDRA.")
    if i == 2:
        par("[[b]]Tabela 3.[[/b]] Estrutura econômica e regimes previdenciários, Campos dos Goytacazes (RJ)",
            indent=False, size=9.5, before=4, after=2)
        tabela(T3, "Fontes: IBGE (Censo 2022, SIDRA 5938, CEMPRE 2024); Siconfi/STN; "
                   "Portal da Transparência de Campos (Despesas por Desdobro, 2020-2025). "
                   "RPPS 2025 = rubrica 31911308. INSS 2025 = rubrica 31901302. (nd = não disponível).")
    if i == 4:
        par("[[b]]Tabela 4.[[/b]] Características das CATs das profissões da saúde, Campos dos Goytacazes (RJ), "
            "2018-2025 (n = 1.144)", indent=False, size=9.5, before=4, after=2)
        tabela(T4, "Fonte dos dados brutos: INSS, CAT, Portal de Dados Abertos (https://dados.gov.br). "
                   "Idade mediana = 36 anos. Sexo ignorado em 4 registros. Um óbito.")
        figura("saidas/figuras/F1_cat_ano_categorias.png",
               "[[b]]Figura 1.[[/b]] CATs de profissões da saúde (n = 1.144) por ano do acidente e categoria "
               "profissional, Campos dos Goytacazes (RJ), 2018-2025. Asterisco indica cobertura parcial ou "
               "irregular da fonte. Fonte dos dados brutos: CAT/INSS, Portal de Dados Abertos.")
        figura("saidas/figuras/F2_serie_mensal_saude.png",
               "[[b]]Figura 2.[[/b]] Distribuição mensal das CATs de profissões da saúde (n = 1.144), "
               "Campos dos Goytacazes (RJ), janeiro de 2018 a dezembro de 2025. Destaque para o período "
               "crítico da covid-19 e médias mensais por período. Fonte dos dados brutos: CAT/INSS.")
        par("[[b]]Tabela 5.[[/b]] Análise de sensibilidade, Campos dos Goytacazes (RJ), 2018-2025",
            indent=False, size=9.5, before=4, after=2)
        tabela(T5, "Fonte dos dados brutos: INSS, CAT, Portal de Dados Abertos. Em todos os cenários "
                   "a hierarquia das categorias manteve-se inalterada.")
    if i == 5:
        par("[[b]]Tabela 6.[[/b]] Testes estatísticos da série temporal de CATs, Campos dos Goytacazes (RJ), "
            "2018-2025", indent=False, size=9.5, before=4, after=2)
        tabela(T6, "Fonte: elaborada pelo autor. Mann-Kendall com correção de ties. "
                   "t-test de Welch para variâncias desiguais. CV = coeficiente de variação.")
        figura("saidas/figuras/F4_tendencia_loess.png",
               "[[b]]Figura 3.[[/b]] Suavização LOESS (fração = 0,30) com intervalo de confiança "
               "[[i]]bootstrap[[/i]] de 200 reamostragens e 95% de confiança, Campos dos Goytacazes (RJ), "
               "2018-2025. Fonte dos dados brutos: CAT/INSS.")
        figura("saidas/figuras/F3_decomposicao_temporal.png",
               "[[b]]Figura 4.[[/b]] Decomposição clássica da série mensal de CATs. Componentes observado, "
               "tendência por média móvel de 12 meses, sazonalidade e resíduo. Área sombreada indica período "
               "crítico da covid-19. Fonte dos dados brutos: CAT/INSS.")
    if i == 6:
        par("[[b]]Tabela 7.[[/b]] Principais regras de associação (Apriori), CATs das profissões da saúde, "
            "Campos dos Goytacazes (RJ), 2018-2025", indent=False, size=9.5, before=4, after=2)
        tabela(T7, "Fonte dos dados brutos: INSS, CAT, Portal de Dados Abertos. Suporte mínimo = 3%. "
                   "Confiança mínima = 30%. Lift mínimo = 1,2. n = 1.144. S61 = ferimento de punho e mão. "
                   "Z20 = exposição a doenças transmissíveis.")
        figura("saidas/figuras/F6_grafo_ocupacao_cid.png",
               "[[b]]Figura 5.[[/b]] Grafo bipartido de associação entre categorias profissionais e grupos "
               "diagnósticos da CID-10. Tamanho do nó proporcional ao número de CATs. Arestas com peso igual "
               "ou superior a três co-ocorrências. Fonte dos dados brutos: CAT/INSS.")

# ======================== REFERÊNCIAS ==========================================
par("[[b]]Referências[[/b]]", indent=False, size=10.5, before=6, after=2)
REFS = [
 "BRASIL. [[b]]Lei nº 8.213, de 24 de julho de 1991[[/b]]. Dispõe sobre os Planos de Benefícios da Previdência Social. Brasília, DF, 1991.",
 "BRASIL. [[b]]Lei nº 9.478, de 6 de agosto de 1997[[/b]]. Dispõe sobre a política energética nacional. Brasília, DF, 1997.",
 "FRANÇA, Maria Júlia Paiva de. O pensamento de Antônio Gramsci na luta pela Saúde do Trabalhador. [[b]]Revista Em Pauta: teoria social e realidade contemporânea[[/b]], "
 "Rio de Janeiro, v. 11, n. 32, p. 89-113, 2014. DOI: 10.12957/rep.2013.10157.",
 "MARTINS, Samuel; HASENCLEVER, Lia; MIRANDA, Caroline. A gestão da saúde à luz da instabilidade de financiamento e das propostas de governo. "
 "[[b]]Cadernos do Desenvolvimento Fluminense[[/b]], Rio de Janeiro, n. 27, 2024. DOI: 10.12957/cdf.2024.87352.",
 "SILVA, J. E. M. da; HASENCLEVER, L. Ciclo do petróleo e desenvolvimento socioeconômico no município de Campos dos Goytacazes "
 "(1999-2014). [[b]]Desenvolvimento em Questão[[/b]], Ijuí, v. 17, n. 46, p. 314-332, 2019. DOI: 10.21527/2237-6453.2019.46.314-332.",
 "SOUZA, D. O.; MELO, A. I. S. C.; VASCONCELLOS, L. C. F. Saúde do(s) trabalhador(es): do 'campo' à 'questão' ou do sujeito sanitário ao sujeito revolucionário. "
 "[[b]]Saúde em Debate[[/b]], Rio de Janeiro, v. 41, n. 113, p. 591-604, abr-jun 2017. DOI: 10.1590/0103-1104201711313.",
 "VEDOVATO, T. G.; ANDRADE, C. B.; SANTOS, D. L.; BITENCOURT, S. M.; ALMEIDA, L. P. de; SAMPAIO, J. F. da S. Trabalhadores(as) da "
 "saúde e a COVID-19: condições de trabalho à deriva? [[b]]Revista Brasileira de Saúde Ocupacional[[/b]], São Paulo, v. 46, e1, 2021. "
 "DOI: 10.1590/2317-6369000028520.",
]
for r in REFS:
    par(r, indent=False, just=False, size=8, after=1)

# ======================== VERIFICAÇÕES =========================================
TRAVESSAO, MEIA_RISCA, DOIS_PONTOS = chr(8212), chr(8211), ":"
conteudo = " ".join(CORPO) + " ".join(REFS)
conteudo += " ".join(v for linha in T1 + T2 + T3 + T4 + T5 + T6 + T7 for v in linha)
for proibido, nome in ((TRAVESSAO, "travessão"), (MEIA_RISCA, "meia-risca")):
    if proibido in conteudo:
        raise SystemExit(f"PROIBIDO: {nome} encontrado no texto.")

os.makedirs("documentos", exist_ok=True)
d.save("documentos/artigo.docx")

soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
if os.path.exists(soffice):
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", "documentos",
                    "documentos/artigo.docx"], capture_output=True, timeout=300)
    from pypdf import PdfReader
    npag = len(PdfReader("documentos/artigo.pdf").pages)
    print(f"artigo.docx gerado com {npag} página(s).")
else:
    print("AVISO: LibreOffice ausente.")
