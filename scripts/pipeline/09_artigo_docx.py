# -*- coding: utf-8 -*-
"""
09_artigo_docx.py — Gera documentos/artigo.docx (A4, margens 2,5 cm, Times New Roman 11,
espaçamento simples, recuo 1,25 cm) e confere o número de páginas via LibreOffice.

Normas aplicadas:
- ABNT NBR 10520:2023 (citações): sobrenomes em caixa alta e baixa no sistema autor-data,
  ex.: (Silva; Hasenclever, 2019); siglas institucionais mantêm-se como siglas (IBGE, 2026).
- ABNT NBR 6023:2025 (referências): título do livro ou do periódico em NEGRITO;
  documentos on-line com "Disponível em: ... Acesso em: ...".
- Sem resumo e sem palavras-chave (decisão editorial do autor).
- PROIBIDO travessão/meia-risca no texto (verificação automática ao final).
- Estrangeirismos em itálico (marcação [[i]]...[[/i]] no texto-fonte).
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
n.paragraph_format.line_spacing = 1.0

def _runs(p, texto, size):
    """Constrói runs a partir de marcação leve: [[i]]itálico[[/i]] e [[b]]negrito[[/b]]."""
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

# ------------------------------ título e autoria ------------------------------
par("[[b]]Comunicações de Acidente de Trabalho nas profissões da saúde em Campos dos "
    "Goytacazes, 2018-2025[[/b]]", indent=False, center=True, size=12, after=4)
par("Ryan de Paulo Santos", indent=False, center=True, size=10.5, after=8)

# ---------------------------------- corpo -------------------------------------
CORPO = [
 # Introdução
 "O trabalho é um processo social, econômico, político e técnico, historicamente determinado, e não apenas um local de exposição a "
 "riscos. Desde a Revolução Industrial, o modo de organizar a produção disciplina corpos e tempos e produz padrões específicos de "
 "adoecimento (OLIVEIRA, 2004). As teses do fim da centralidade do trabalho não se confirmaram: houve deslocamento da classe "
 "trabalhadora para o setor de serviços, no qual hoje se concentram precarização, terceirização e intensificação (LOURENÇO, 2012; "
 "ANTUNES, 2018). No Brasil, o campo da Saúde do Trabalhador constituiu-se como crítica à medicina do trabalho e à saúde ocupacional, "
 "ao afirmar a determinação social do processo saúde-doença e o processo de trabalho como categoria explicativa central (MENDES; DIAS, "
 "1991). No setor saúde, essa perspectiva exige considerar que o trabalho produtor do cuidado se realiza sob divisão social e técnica "
 "do trabalho, relações desiguais de poder entre categorias, cargas de trabalho e desgaste, em serviços submetidos à reorganização "
 "gerencial flexível e à desproteção de parcela expressiva dos vínculos do Sistema Único de Saúde (SUS), estimada entre 30% e 50% "
 "(CECILIO; LACAZ, 2012). Este artigo analisa, à luz da formação histórico-social e econômica de Campos dos Goytacazes (RJ), o perfil "
 "das Comunicações de Acidente de Trabalho (CAT) vinculadas a empregadores do município entre as diferentes profissões da saúde, no "
 "período de 2018 a 2025.",

 # Campos
 "Campos dos Goytacazes é o maior município fluminense em extensão (4.032,5 km²) e contava com 483.540 habitantes no Censo de 2022 "
 "(IBGE, 2026). Sua formação econômica assentou-se na agroindústria açucareira, organizada desde o período colonial sobre a grande "
 "propriedade e o trabalho escravizado e, posteriormente, sobre as usinas; ao longo do século XX essa base entrou em prolongada "
 "decadência e, a partir das décadas de 1980 e 1990, cedeu lugar à centralidade da exploração de petróleo da Bacia de Campos e das "
 "rendas petrolíferas ([[i]]royalties[[/i]] e participações especiais) (SILVA; HASENCLEVER, 2019). Os dados oficiais evidenciam uma "
 "economia oscilante e dependente (Tabela 1): o produto interno bruto, a preços correntes, atingiu R$ 58,4 bilhões em 2013, caiu para "
 "R$ 23,9 bilhões em 2020 e retornou a R$ 43,0 bilhões em 2023; a indústria, dominada pela atividade extrativa, respondeu por 66,4% do "
 "valor adicionado em 2013 e por 40,8% em 2020; a agropecuária, apesar da identidade agrária do discurso local, representou 1,0% em "
 "2021, com a produção de cana reduzida de 4,28 milhões de toneladas em 2005 para 1,29 milhão em 2023 (IBGE, 2026). Silva e "
 "Hasenclever (2019) demonstram que o ciclo do petróleo elevou arrecadação e produto sem diversificação produtiva nem desenvolvimento "
 "social equivalentes; Martins, Hasenclever e Miranda (2024) mostram que o financiamento da saúde municipal acompanhou as flutuações "
 "das rendas petrolíferas entre 2009 e 2020, fragilizando a gestão da rede. Nesse mercado de trabalho, os serviços de saúde, polo "
 "regional de referência do Norte Fluminense, constituem espaço relevante de assalariamento, sobretudo feminino, estratificado por "
 "hierarquias de renda e de prestígio entre profissões, próximas do que a sociologia weberiana descreve como situações de classe e de "
 "estamento (LEMOS, 2012).",

 # Método
 "[[b]]Método.[[/b]] Estudo teórico-conceitual e documental, apoiado em dados secundários públicos, com [[i]]pipeline[[/i]] "
 "reprodutível, auditado e validado de forma independente (scripts, logs e testes automatizados acompanham o repositório do estudo). "
 "A base empírica foi reconstruída dos arquivos brutos dos dados abertos da CAT do Instituto Nacional do Seguro Social (INSS): 58 "
 "arquivos, competências de julho de 2018 a dezembro de 2025, totalizando 3.902.905 registros (BRASIL, 2026a). A importação foi feita "
 "por posição de coluna, porque a fonte apresenta quatro esquemas estruturais distintos e cabeçalhos duplicados (CBO, CID-10, CNAE e "
 "data do acidente); a codificação de caracteres foi detectada arquivo a arquivo; e o mês de referência administrativo (coluna 2) foi "
 "rigorosamente distinguido da data completa do acidente, única informação usada nas análises temporais. O recorte municipal exigiu, "
 "simultaneamente, código do município do empregador igual a 330100, extraído antes do hífen, e unidade federativa do empregador igual "
 "a Rio de Janeiro; municípios homônimos (Campos Novos, Campos do Jordão, Campos de Júlio, São José dos Campos, entre outros) foram "
 "identificados e excluídos, assim como 12 registros com unidade federativa divergente. Foram removidas 537 duplicidades exatas entre "
 "arquivos de cobertura sobreposta, demonstradas por resumo criptográfico ([[i]]hash[[/i]] SHA-256) da linha bruta; duplicatas dentro "
 "de um mesmo arquivo foram mantidas e sinalizadas, por poderem representar eventos legítimos. A classificação ocupacional utilizou os "
 "códigos de seis dígitos da Classificação Brasileira de Ocupações (CBO 2002), com dicionário auditado dos 459 códigos observados e "
 "três níveis de análise: universo principal das profissões da saúde; profissões multiprofissionais de atuação intersetorial "
 "(psicologia, serviço social, educação física e biologia), analisadas à parte; e trabalhadores de apoio em estabelecimentos de saúde, "
 "jamais somados às profissões da saúde. Registros sem código válido (184; 3,6%) foram mantidos em categoria própria e quantificados. "
 "Denominadores de força de trabalho foram extraídos do Cadastro Nacional de Estabelecimentos de Saúde (CNES): profissionais por "
 "ocupação, em dezembro de cada ano, no município (BRASIL, 2026b); como o CNES abrange vínculos estatutários, autônomos e de pessoa "
 "jurídica, não cobertos pela CAT, tais denominadores sustentam apenas razões exploratórias de densidade de comunicação, e não medidas "
 "de incidência ou de risco. Todos os totais foram reproduzidos por rotina independente, com convergência integral; células com menos "
 "de cinco registros foram agregadas; as análises de sensibilidade abrangeram exclusão de 2025 (ano parcial, com dados até outubro), "
 "restrição aos meses de janeiro a outubro em todos os anos, exclusão de acidentes de trajeto, restrição a acidentes típicos e "
 "restrição a empregadores das divisões 86 e 87 da CNAE.",

 # Resultados
 "[[b]]Resultados.[[/b]] Das 5.066 CATs vinculadas a empregadores de Campos dos Goytacazes entre 2018 e 2025, 1.144 (22,6%) "
 "correspondem ao universo principal das profissões da saúde, 26 às profissões multiprofissionais, 184 (3,6%) a registros sem CBO "
 "válido e 3.712 às demais ocupações (427 delas empregadas em estabelecimentos de saúde). A distribuição interna é fortemente "
 "assimétrica (Tabela 2): a enfermagem concentra 84,4% dos registros do universo principal, sendo 70,2% de técnicos e auxiliares e "
 "14,2% de enfermeiros; seguem-se os técnicos e auxiliares de diagnóstico e laboratório (6,8%) e a fisioterapia (2,6%); a medicina "
 "responde por 1,0%. Predominam mulheres (85,7%), com idade mediana de 36 anos. Os acidentes típicos somam 81,9% e os de trajeto, "
 "17,1%. Os ferimentos de punho e mãos lideram os diagnósticos (código S61 da CID-10: 25,1%; o dedo é a parte atingida em 43,9% dos "
 "registros), seguidos do contato ou exposição a doenças transmissíveis (Z20: 21,9%); agentes infecciosos e produtos biológicos "
 "respondem por 26,9% dos agentes causadores. Quase todos os empregadores pertencem às divisões 86 e 87 da CNAE (95,4%), com "
 "dominância hospitalar (classe 8610: 76,8%). O empregador emitiu 97,0% das CATs, com mediana de um dia entre o acidente e a emissão; "
 "houve um óbito registrado. Comunicações de doença relacionada ao trabalho somaram apenas 1,0%, mesmo com a pandemia dentro do "
 "período de análise (Figuras 1 e 2).",

 # Discussão
 "[[b]]Discussão.[[/b]] A concentração dos registros na base técnica da enfermagem não deve ser lida como simples somatório de riscos "
 "biológicos ou ergonômicos: ela expressa a divisão social e técnica do trabalho em saúde, na qual a execução manual, contínua e "
 "corporal do cuidado (punção venosa, administração de medicamentos, manipulação de perfurocortantes, mobilização de pacientes) é "
 "delegada a categorias majoritariamente femininas, de menor renda e prestígio, submetidas a sobrecarga e intensificação, das quais "
 "deriva o desgaste (CECILIO; LACAZ, 2012; ANTUNES, 2018). A quase invisibilidade da medicina (12 CATs em oito anos, ante 1.360 a "
 "1.702 médicos ativos no CNES) não autoriza concluir menor exposição: indica inserção por vínculos estatutários, autônomos e de "
 "pessoa jurídica, situados fora do emprego celetista coberto pela CAT, o que configura desigualdade de proteção e de reconhecimento "
 "institucional e reitera, no plano previdenciário, a estratificação de classe e de prestígio entre as profissões (LEMOS, 2012). Pela "
 "mesma razão, agentes comunitários de saúde e agentes de combate às endemias, majoritariamente vinculados à administração pública "
 "municipal, quase não aparecem na base (14 registros; nenhum agente de combate às endemias), sem que se possa inferir ausência de "
 "adoecimento. A elevação da média mensal de registros no período crítico da covid-19 (de 10,7 para 14,5, com 11,9 no período "
 "posterior) e o peso das exposições biológicas são compatíveis com a sobrecarga pandêmica descrita para os trabalhadores da saúde, "
 "marcada por déficit de proteção e de reconhecimento (VEDOVATO et al., 2021); oscilações de cobertura da própria fonte, "
 "contudo, impedem qualquer atribuição causal (Figura 2). A baixíssima frequência de comunicações de doença (1,0%) reforça o "
 "diagnóstico de subnotificação seletiva: o sistema registra sobretudo a lesão aguda e visível, e não o adoecimento lento produzido "
 "pela organização do trabalho.",

 "Os dados permitem descrever a estrutura interna das comunicações registradas: quem aparece, com que lesões, em que vínculos e em "
 "que estabelecimentos. Não permitem estimar incidência, prevalência ou risco ocupacional, pois as diferenças entre categorias podem "
 "refletir o tamanho das forças de trabalho, a composição e a formalização dos vínculos, a terceirização, a cobertura previdenciária, "
 "a cultura institucional de notificação e a subnotificação diferencial. A robustez interna dos achados é alta: a predominância da "
 "enfermagem e a hierarquia das categorias mantêm-se em todos os cenários de sensibilidade, com participação da enfermagem entre "
 "84,4% e 86,3%. As razões exploratórias com denominadores do CNES (9.803 profissionais em 2018; 13.275 em 2025) reforçam o "
 "gradiente: nos anos de cobertura integral (2019 a 2021 e 2023) houve de 29,5 a 43,5 CATs por 1.000 técnicos e auxiliares de "
 "enfermagem ao ano, de 19,4 a 32,7 por 1.000 enfermeiros e, na medicina, no máximo 3,6 (valores suprimidos nos demais anos por "
 "contagens inferiores a cinco). Vínculos formais da Relação Anual de Informações Sociais (RAIS) por ocupação, município e ano "
 "permanecem como denominador prioritário para indicadores padronizados, condicionados à demonstração de compatibilidade entre "
 "numerador e denominador.",

 # Considerações finais
 "[[b]]Considerações finais.[[/b]] Para a Vigilância em Saúde do Trabalhador e para a gestão municipal, os resultados indicam "
 "prioridades verificáveis: proteger a base técnica da enfermagem, núcleo do cuidado e dos registros, com ênfase em perfurocortantes "
 "e exposição biológica; enfrentar a subnotificação de doenças relacionadas ao trabalho e a invisibilidade de estatutários, "
 "terceirizados e informais, articulando CAT, RAIS, CNES e as notificações do SUS; qualificar o preenchimento dos registros, pois "
 "3,6% não trazem código ocupacional válido, com concentração entre 2021 e 2023; e planejar a rede assistencial reconhecendo que seu "
 "financiamento oscila com as rendas petrolíferas (MARTINS; HASENCLEVER; MIRANDA, 2024) e que a proteção de quem cuida é condição de "
 "possibilidade do próprio cuidado.",

 # Limitações
 "[[b]]Limitações.[[/b]] A CAT capta comunicações, e não a totalidade dos acidentes e adoecimentos; cobre essencialmente o emprego "
 "formal celetista, excluindo trabalhadores informais, autônomos e estatutários; não há denominadores plenamente compatíveis para o "
 "cálculo de incidência, e as razões com o CNES são exploratórias, porque o denominador inclui vínculos não cobertos pela CAT; a "
 "cobertura da fonte é parcial em 2018 (competências desde julho), irregular em 2022, atípica de setembro a dezembro de 2024 e "
 "incompleta em 2025 (dados até outubro), o que restringe comparações anuais; registros sem CBO válido podem subestimar as profissões "
 "da saúde entre 2021 e 2023; e o desenho descritivo e documental não permite inferência causal.",
]

# Tabela 1 após o parágrafo 2; Tabela 2 e Figuras após o parágrafo 4 (Resultados)
def tabela(dados_tab, fonte_txt, largs=None):
    t = d.add_table(rows=0, cols=len(dados_tab[0])); t.style = "Table Grid"
    for i, row in enumerate(dados_tab):
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].text = ""
            _runs(cells[j].paragraphs[0], v, 8.5)
            for r_ in cells[j].paragraphs[0].runs:
                r_.bold = r_.bold or (i == 0)
    par(fonte_txt, indent=False, size=8.5, after=4)

T1 = [
 ("Indicador", "Valores", "Fonte (IBGE/SIDRA)"),
 ("População residente (2022); área; densidade", "483.540 hab.; 4.032,5 km²; 119,9 hab./km²", "Censo 2022 (tabela 4714)"),
 ("PIB a preços correntes", "R$ 58,4 bi (2013); R$ 23,9 bi (2020); R$ 43,0 bi (2023)", "PIB dos Municípios (tabela 5938)"),
 ("Participação da indústria (extrativa) no valor adicionado", "66,4% (2013); 40,8% (2020)", "PIB dos Municípios (tabela 5938)"),
 ("Participação da agropecuária no valor adicionado (2021)", "1,0%", "PIB dos Municípios (tabela 5938)"),
 ("Cana-de-açúcar: quantidade produzida", "4,28 milhões t (2005); 1,29 milhão t (2023)", "PAM (tabela 1612)"),
]
T2 = [
 ("Característica", "n (%)"),
 ("Técnicos e auxiliares de enfermagem", "803 (70,2)"),
 ("Enfermeiros", "163 (14,2)"),
 ("Técnicos e auxiliares de diagnóstico e laboratório", "78 (6,8)"),
 ("Fisioterapia", "30 (2,6)"),
 ("Técnicos e auxiliares de farmácia", "20 (1,7)"),
 ("Agentes comunitários de saúde e afins", "14 (1,2)"),
 ("Medicina", "12 (1,0)"),
 ("Demais categorias (farmácia, nutrição, odontologia e saúde bucal, fonoaudiologia, instrumentação cirúrgica; n<5 agregados)", "24 (2,1)"),
 ("Sexo feminino", "980 (85,7)"),
 ("Acidente típico; de trajeto; doença", "937 (81,9); 196 (17,1); 11 (1,0)"),
 ("Parte do corpo atingida: dedo", "502 (43,9)"),
 ("Agente causador biológico ou infeccioso", "308 (26,9)"),
 ("CID-10 S61 (ferimento de punho e mão); Z20 (exposição a doenças transmissíveis)", "287 (25,1); 250 (21,9)"),
 ("Empregador nas divisões CNAE 86 e 87 (na classe 8610, hospitalar)", "1.091 (95,4); 879 (76,8)"),
 ("CAT emitida pelo empregador; mediana acidente-emissão de 1 dia", "1.110 (97,0)"),
]

def figura(path, caption):
    pf = d.add_paragraph(); pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.paragraph_format.space_before = Pt(4)
    pf.add_run().add_picture(path, width=Cm(14.5))
    par(caption, indent=False, size=8.5, after=4)

# montagem: parágrafos 1-2, Tabela 1, parágrafos 3-4, Tabela 2, Figuras, parágrafos 5-8
for i, texto in enumerate(CORPO):
    par(texto, after=2)
    if i == 1:
        par("[[b]]Tabela 1.[[/b]] Campos dos Goytacazes (RJ): síntese da formação econômica e social",
            indent=False, size=9.5, before=4, after=2)
        tabela(T1, "Fonte: elaborada pelo autor a partir de IBGE (2026); valores correntes, sem deflacionamento; "
                   "interpretação histórica conforme Silva e Hasenclever (2019).")
    if i == 3:
        par("[[b]]Tabela 2.[[/b]] Características das CATs das profissões da saúde, empregadores de Campos dos "
            "Goytacazes (RJ), 2018-2025 (n = 1.144)", indent=False, size=9.5, before=4, after=2)
        tabela(T2, "Fonte: elaborada pelo autor a partir de Brasil (2026a). Idade mediana de 36 anos; sexo ignorado em "
                   "4 registros; um óbito registrado. Percentuais sobre o total do universo principal.")
        figura("saidas/figuras/F1_cat_ano_categorias.png",
               "[[b]]Figura 1.[[/b]] CATs de profissões da saúde (universo principal, n = 1.144) vinculadas a empregadores de "
               "Campos dos Goytacazes (RJ), por ano do acidente e categoria profissional, 2018-2025. Unidade: registros. "
               "Fonte: elaborada pelo autor a partir de Brasil (2026a). *Cobertura parcial ou irregular da fonte (2018: "
               "competências desde julho; 2022: carga irregular; 2024: setembro a dezembro atípicos; 2025: até outubro). "
               "Frequências de comunicação, não taxas de acidente.")
        figura("saidas/figuras/F2_serie_mensal_saude.png",
               "[[b]]Figura 2.[[/b]] Distribuição mensal das CATs de profissões da saúde (universo principal, n = 1.144), "
               "empregadores de Campos dos Goytacazes (RJ), janeiro de 2018 a dezembro de 2025, com destaque para o período "
               "crítico da covid-19 (março de 2020 a dezembro de 2021) e médias mensais por período. Unidade: registros por mês. "
               "Fonte: elaborada pelo autor a partir de Brasil (2026a). As oscilações também refletem a cobertura da fonte "
               "(ver notas da Figura 1).")

# ------------------------------- referências ----------------------------------
par("[[b]]Referências[[/b]]", indent=False, size=10.5, before=4, after=2)
REFS = [
 "ANTUNES, R. [[b]]O privilégio da servidão[[/b]]: o novo proletariado de serviços na era digital. São Paulo: Boitempo, 2018.",
 "BRASIL. Instituto Nacional do Seguro Social. [[b]]Comunicações de Acidente de Trabalho (CAT)[[/b]]: dados abertos, competências de "
 "julho de 2018 a dezembro de 2025. Brasília, DF: INSS, 2026a. Disponível em: "
 "https://dados.gov.br/dados/conjuntos-dados/inss-comunicacao-de-acidente-de-trabalho-cat. Acesso em: 18 jul. 2026.",
 "BRASIL. Ministério da Saúde. DATASUS. [[b]]CNES: recursos humanos, profissionais, indivíduos, segundo CBO 2002, Rio de "
 "Janeiro[[/b]]. Brasília, DF: Ministério da Saúde, 2026b. Disponível em: http://tabnet.datasus.gov.br. Acesso em: 18 jul. 2026.",
 "CECILIO, L. C. O.; LACAZ, F. A. C. [[b]]O trabalho em saúde[[/b]]. Rio de Janeiro: Cebes, 2012.",
 "IBGE. [[b]]Sistema IBGE de Recuperação Automática (SIDRA)[[/b]]: Censo Demográfico 2022 (tabela 4714); Produto Interno Bruto dos "
 "Municípios (tabela 5938); Produção Agrícola Municipal (tabela 1612). Rio de Janeiro: IBGE, 2026. Disponível em: "
 "https://sidra.ibge.gov.br. Acesso em: 18 jul. 2026.",
 "LEMOS, M. R. Estratificação social na teoria de Max Weber: considerações em torno do tema. [[b]]Revista Iluminart[[/b]], "
 "Sertãozinho, ano 4, n. 9, p. 113-128, nov. 2012.",
 "LOURENÇO, G. G. O fim do fim do trabalho: uma crítica à chamada sociedade pós-industrial e sua relação com os movimentos de "
 "trabalhadores. [[b]]Primeiros Estudos[[/b]], São Paulo, n. 3, p. 104-121, 2012. Disponível em: "
 "https://doi.org/10.11606/issn.2237-2423.v0i3p104-121. Acesso em: 18 jul. 2026.",
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
    par(r, indent=False, just=False, size=9.5, after=2)

# --------------------- verificação de travessão/meia-risca ---------------------
TRAVESSAO, MEIA_RISCA = chr(8212), chr(8211)
conteudo = " ".join(CORPO) + " ".join(REFS) + " ".join(v for linha in T1 + T2 for v in linha)
for proibido, nome in ((TRAVESSAO, "travessão"), (MEIA_RISCA, "meia-risca")):
    if proibido in conteudo:
        raise SystemExit(f"PROIBIDO: {nome} encontrado no texto do artigo.")

os.makedirs("documentos", exist_ok=True)
d.save("documentos/artigo.docx")

# ---------------------- verificação de páginas (≤ 5) ---------------------------
soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
if os.path.exists(soffice):
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", "documentos", "documentos/artigo.docx"],
                   capture_output=True, timeout=300)
    from pypdf import PdfReader
    npag = len(PdfReader("documentos/artigo.pdf").pages)
    print(f"artigo.docx gerado (sem travessao) com {npag} pagina(s) no PDF de verificacao.")
    if npag > 5:
        raise SystemExit("LIMITE EXCEDIDO: artigo com mais de 5 paginas.")
else:
    print("AVISO: LibreOffice ausente; numero de paginas NAO verificado nesta maquina.")
