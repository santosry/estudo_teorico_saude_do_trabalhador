# -*- coding: utf-8 -*-
"""09_artigo_docx.py — Gera documentos/artigo.docx (A4, margens 2,5 cm, TNR 11,
espaçamento simples, recuo de 1,25 cm) e confere o nº de páginas via LibreOffice."""
import os, subprocess, glob
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

def p_txt(t, indent=True, just=True, size=11, bold=False, before=0, after=0, italic=False):
    p = d.add_paragraph()
    r = p.add_run(t)
    r.font.size = Pt(size); r.bold = bold; r.italic = italic
    pf = p.paragraph_format
    pf.first_line_indent = Cm(1.25) if indent else Cm(0)
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if just: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

# ---------- título ----------
t = d.add_paragraph()
r = t.add_run("Saúde do trabalhador em Campos dos Goytacazes: formação histórico-social e perfil das "
              "comunicações de acidentes de trabalho entre profissões da saúde, 2018–2025")
r.bold = True; r.font.size = Pt(12)
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
t.paragraph_format.space_after = Pt(6)

# ---------- resumo ----------
p_txt("Resumo: Objetivou-se analisar, à luz da formação histórico-social e econômica de Campos dos Goytacazes (RJ), o perfil das "
      "Comunicações de Acidente de Trabalho (CAT) vinculadas a empregadores do município entre as profissões da saúde, de 2018 a 2025. "
      "Estudo teórico-conceitual, com análise documental e dados secundários: fontes teóricas da Saúde do Trabalhador e da sociologia do "
      "trabalho, caracterização municipal (IBGE) e reconstrução integral e auditada dos dados abertos da CAT/INSS (58 arquivos; 3.902.905 "
      "registros), com filtro pelo código do município do empregador (330100) e UF, classificação ocupacional por códigos CBO 2002 e validação "
      "independente. Identificaram-se 5.066 CATs de empregadores do município, das quais 1.144 (22,6%) de profissões da saúde: 84,4% da "
      "enfermagem (70,2% de técnicos e auxiliares) e apenas 1,0% da medicina; predominaram mulheres (85,7%), acidentes típicos (81,9%), "
      "ferimentos de dedos e mãos e exposição a material biológico (26,9%); doenças relacionadas ao trabalho somaram 1,0%. A média mensal de "
      "registros elevou-se no período crítico da covid-19. O padrão expressa a divisão social e técnica do trabalho em saúde e desigualdades de "
      "proteção e de notificação conformadas pela trajetória econômica local, marcada pela transição do açúcar ao petróleo e pela dependência "
      "fiscal. Frequências de registro não medem risco; recomenda-se qualificar registros e incorporar denominadores (RAIS/CNES) à vigilância.",
      indent=False, size=10, after=2)
p_txt("Palavras-chave: Saúde do Trabalhador; Acidentes de Trabalho; Notificação de Acidentes de Trabalho; Pessoal de Saúde; Desenvolvimento Regional.",
      indent=False, size=10, after=6)

# ---------- corpo ----------
corpo = [
 "O trabalho, entendido como processo social, econômico, político e técnico — e não como mero local de exposição a riscos —, é "
 "historicamente determinado: da disciplinarização fabril inaugurada pela Revolução Industrial às reconfigurações contemporâneas, o modo de "
 "organizar a produção modela corpos, tempos e adoecimentos (OLIVEIRA, 2004). As teses do “fim do trabalho” não se sustentam: o que houve foi "
 "deslocamento e ampliação da classe trabalhadora para os serviços, setor em que hoje se concentram precarização, terceirização e intensificação "
 "(LOURENÇO, 2012; ANTUNES, 2018). No Brasil, o campo da Saúde do Trabalhador constituiu-se, a partir da crítica à medicina do trabalho e à "
 "saúde ocupacional, como leitura da determinação social do processo saúde-doença ancorada no processo de trabalho e no protagonismo dos "
 "trabalhadores (MENDES; DIAS, 1991). No setor saúde, esse referencial ganha densidade: o trabalho em saúde produz cuidado, mas se realiza sob "
 "divisão social e técnica do trabalho, relações de poder entre categorias, cargas e desgaste, num contexto de reorganização gerencial-flexível "
 "dos serviços em que parcela expressiva dos vínculos do SUS — estimada entre 30% e 50% — carece de proteção plena de direitos "
 "(CECILIO; LACAZ, 2012). Este artigo analisa, à luz da formação histórico-social e econômica de Campos dos Goytacazes (RJ), o perfil das CATs "
 "vinculadas a empregadores do município entre as diferentes profissões da saúde, de 2018 a 2025.",

 "Campos dos Goytacazes, maior município fluminense em extensão (4.032,5 km²; 483.540 habitantes no Censo 2022), formou-se sobre a "
 "economia açucareira colonial — engenhos e depois usinas assentados em concentração fundiária e no trabalho escravizado — e conheceu, ao longo "
 "do século XX, a decadência da agroindústria canavieira, substituída, desde os anos 1980-1990, pela centralidade da exploração de petróleo da "
 "Bacia de Campos e das rendas petrolíferas (SILVA; HASENCLEVER, 2019). Os dados oficiais evidenciam uma economia oscilante e dependente: o PIB "
 "a preços correntes saltou a R$ 58,4 bilhões em 2013, caiu a R$ 23,9 bilhões em 2020 e retornou a R$ 43,0 bilhões em 2023; a indústria "
 "(dominada pela atividade extrativa) respondeu por 66,4% do valor adicionado em 2013 e 40,8% em 2020, enquanto a agropecuária — apesar da "
 "identidade “agro” do discurso local — representou apenas 1,0% em 2021, com a produção de cana caindo de 4,28 milhões de toneladas (2005) para "
 "1,29 milhão (2023) (IBGE, 2026). Silva e Hasenclever (2019) demonstram que o ciclo do petróleo (1999-2014) elevou arrecadação e PIB sem "
 "diversificação produtiva correspondente nem desenvolvimento social equivalente — riqueza fiscal convivendo com desigualdade e emprego "
 "concentrado em serviços de baixa remuneração. Essa contradição alcança diretamente a saúde: o financiamento municipal acompanhou as "
 "flutuações das rendas de indenizações petrolíferas entre 2009 e 2020, fragilizando a gestão da rede (MARTINS; HASENCLEVER; MIRANDA, 2024). "
 "Nesse mercado de trabalho, os serviços de saúde — polo regional de referência do Norte Fluminense — constituem importante espaço de "
 "assalariamento, sobretudo feminino, estratificado por hierarquias de renda, prestígio e fechamento social entre profissões, na acepção "
 "weberiana de classe e estamento (LEMOS, 2012).",

 "Método. Estudo teórico-conceitual e documental com apoio de dados secundários. A base empírica foi reconstruída integralmente a partir "
 "dos 58 arquivos brutos dos dados abertos da CAT/INSS (competências de jul./2018 a dez./2025; 3.902.905 linhas) (BRASIL, 2026a), importados por "
 "posição ante quatro esquemas estruturais com cabeçalhos duplicados (CBO, CID-10, CNAE, “Data Acidente”), codificação detectada por arquivo e "
 "distinção estrita entre o mês de referência (coluna 2) e a data completa do acidente, usada nas análises temporais. O filtro municipal exigiu, "
 "simultaneamente, código do município do empregador igual a 330100 (extraído antes do hífen) e UF do empregador Rio de Janeiro, excluindo-se "
 "homônimos (Campos Novos, Campos do Jordão, Campos de Júlio, São José dos Campos etc.) e 12 registros com UF divergente. Removeram-se 537 "
 "duplicidades exatas entre arquivos de cobertura sobreposta (hash SHA-256 da linha bruta). A classificação ocupacional baseou-se nos códigos "
 "CBO 2002 de seis dígitos, com dicionário mestre auditado dos 459 códigos observados e três níveis: universo principal das profissões da saúde "
 "(medicina, enfermagem, odontologia/saúde bucal, farmácia, fisioterapia, nutrição, fonoaudiologia, técnicos e auxiliares de diagnóstico e "
 "laboratório, agentes comunitários e afins, instrumentação cirúrgica); profissões multiprofissionais intersetoriais (psicologia, serviço "
 "social, educação física, biologia), analisadas à parte com sensibilidade restrita a empregadores de CNAE 86/87; e trabalhadores de apoio em "
 "estabelecimentos de saúde, jamais somados às profissões da saúde. Registros sem CBO válido (184; 3,6%) foram mantidos em categoria própria. "
 "Denominadores de força de trabalho foram extraídos do CNES/DataSUS — profissionais (indivíduos) por ocupação, em dezembro de "
 "cada ano, no município (BRASIL, 2026b) —, mas, por incluírem vínculos estatutários, autônomos e de pessoa jurídica não cobertos "
 "pela CAT, sustentam apenas razões exploratórias de densidade de comunicação, e não incidência; no mais, apresentam-se "
 "frequências e proporções dentro do conjunto de CATs, com agregação de células n<5. Os totais foram reproduzidos por rotina "
 "independente, com convergência integral; análises de sensibilidade abrangeram exclusão de 2025 (parcial, até out.), meses "
 "equivalentes, exclusão de trajeto, somente típicos e universo restrito a CNAE 86/87.",

 "Das 5.066 CATs de empregadores de Campos, 1.144 (22,6%) referem-se ao universo principal das profissões da saúde — proporção que, "
 "por si, indica o peso do polo assistencial no emprego formal celetista local. A distribuição interna (Tabela 2) é fortemente assimétrica: a "
 "enfermagem concentra 84,4% dos registros (técnicos e auxiliares, 70,2%; enfermeiros, 14,2%), seguida de técnicos e auxiliares de diagnóstico "
 "e laboratório (6,8%) e fisioterapia (2,6%); a medicina soma 1,0%. Predominam mulheres (85,7%), idade mediana de 36 anos, acidentes típicos "
 "(81,9%; trajeto, 17,1%), ferimentos de punho e mãos (CID S61, 25,1%; “dedo” como parte atingida, 43,9%) e contato/exposição a doenças "
 "transmissíveis (Z20, 21,9%); agentes infecciosos e produtos biológicos respondem por 26,9% dos agentes causadores. Quase a totalidade dos "
 "empregadores pertence às divisões CNAE 86/87 (95,4%), com franca dominância hospitalar (classe 8610: 76,8%) — quadro coerente com a função "
 "de polo regional. O empregador emitiu 97,0% das CATs, com mediana de um dia entre acidente e emissão; registrou-se um óbito. Registros de "
 "“doença” somaram apenas 1,0%, mesmo atravessando a pandemia — indício robusto de subnotificação das doenças relacionadas ao trabalho.",

 "A leitura teórica desses achados recusa a redução do problema a uma lista de riscos biológicos ou ergonômicos. A concentração dos "
 "registros na base técnica da enfermagem expressa a divisão social e técnica do trabalho em saúde: a execução manual, contínua e corporal do "
 "cuidado — punção, medicação, manipulação de perfurocortantes, mobilização de pacientes — é delegada às categorias femininas de menor renda e "
 "prestígio, submetidas a sobrecarga, dupla jornada e intensificação, das quais deriva o desgaste (CECILIO; LACAZ, 2012; ANTUNES, 2018). Já a "
 "quase invisibilidade da medicina (12 CATs em oito anos) não autoriza concluir menor exposição: reflete, antes, a inserção médica por vínculos "
 "estatutários, autônomos e de pessoa jurídica, à margem do emprego celetista coberto pela CAT — desigualdade de proteção e de reconhecimento "
 "institucional que reitera, no plano previdenciário, a estratificação de classe e status entre as profissões (LEMOS, 2012). Pela mesma razão, "
 "agentes comunitários de saúde e de combate às endemias, majoritariamente vinculados à administração municipal, praticamente inexistem na base "
 "(14 registros de ACS e afins; nenhum ACE), sem que se possa inferir ausência de adoecimento. A elevação da média mensal de registros no "
 "período crítico da covid-19 (10,7 em jan./2018-fev./2020; 14,5 em mar./2020-dez./2021; 11,9 após) e o peso das exposições biológicas são "
 "compatíveis com a sobrecarga pandêmica descrita para os trabalhadores da saúde — condições de trabalho “à deriva”, com déficit de proteção e "
 "reconhecimento (VEDOVATO et al., 2021) —, mas oscilações de cobertura da própria fonte impedem qualquer atribuição causal (Figura 1).",

 "Os dados permitem afirmar a estrutura interna das comunicações registradas — quem aparece, com quais lesões, em quais vínculos e "
 "estabelecimentos —, e não permitem estimar incidência, prevalência ou risco ocupacional: diferenças entre categorias podem refletir tamanho "
 "das forças de trabalho, composição e formalização dos vínculos, terceirização, cobertura previdenciária, cultura institucional e "
 "subnotificação diferencial. A robustez interna é alta: a predominância da enfermagem e a hierarquia das categorias mantêm-se em todas "
 "as análises de sensibilidade — exclusão de 2025, meses jan.–out., exclusão de trajeto, somente típicos e restrição a CNAE 86/87 "
 "(participação da enfermagem entre 84,4% e 86,3%). Denominadores reais do CNES/DataSUS — profissionais por ocupação em dezembro de "
 "cada ano, de 9.803 (2018) a 13.275 (2025) no município (BRASIL, 2026b) — permitem uma razão exploratória de densidade de comunicação, "
 "jamais de incidência, pois o CNES inclui vínculos estatutários, autônomos e de pessoa jurídica, fora da cobertura da CAT: nos anos de "
 "cobertura integral (2019–2021 e 2023), houve 29,5 a 43,5 CATs por 1.000 técnicos e auxiliares de enfermagem ao ano, 19,4 a 32,7 por "
 "1.000 enfermeiros e, na medicina, no máximo 3,6 (2019; demais anos suprimidos por n<5) — gradiente que reforça a leitura de proteção "
 "e notificação desiguais entre as categorias. Vínculos formais da RAIS/eSocial por CBO, município e ano permanecem como denominador "
 "prioritário para indicadores padronizados, condicionados à verificação de compatibilidade entre numerador e denominador.",

 "Considerações finais. Para a Vigilância em Saúde do Trabalhador e a gestão municipal, os resultados indicam prioridades concretas: "
 "proteger a base técnica da enfermagem — núcleo do cuidado e dos registros —, com ênfase em perfurocortantes e exposição biológica; enfrentar a "
 "subnotificação de doenças relacionadas ao trabalho e a invisibilidade de estatutários, terceirizados e informais, articulando CAT, RAIS, CNES "
 "e as notificações do SUS; qualificar o preenchimento (3,6% dos registros sem CBO válido, concentrados em 2021-2023); e planejar a rede — cuja "
 "sustentação financeira oscila com as rendas petrolíferas (MARTINS; HASENCLEVER; MIRANDA, 2024) — reconhecendo que a proteção dos que cuidam é "
 "condição do cuidado. Limitações: a CAT capta comunicações, não a totalidade dos acidentes; cobre essencialmente o emprego formal celetista, "
 "excluindo informais, autônomos e estatutários; não há denominadores compatíveis para incidência — as razões com o CNES são "
 "exploratórias, pois o denominador inclui vínculos não celetistas —; a cobertura da fonte é parcial em 2018 (competências desde "
 "jul.), irregular em 2022, atípica em set.-dez./2024 e incompleta em 2025 (até out.), o que restringe comparações anuais; registros sem CBO "
 "podem subestimar profissões da saúde em 2021-2023; e o desenho descritivo-documental não permite inferência causal.",
]
for par in corpo:
    p_txt(par, after=2)

# ---------- Tabela 1 ----------
p_txt("Tabela 1 – Campos dos Goytacazes (RJ): síntese da formação econômica e social", indent=False, size=9.5, bold=True, before=4, after=2)
t1 = [
 ("Indicador", "Valores", "Fonte (IBGE/SIDRA)"),
 ("População residente (2022); área; densidade", "483.540 hab.; 4.032,5 km²; 119,9 hab./km²", "Censo 2022 (tab. 4714)"),
 ("PIB a preços correntes", "R$ 58,4 bi (2013); R$ 23,9 bi (2020); R$ 43,0 bi (2023)", "PIB dos Municípios (tab. 5938)"),
 ("Participação da indústria (extrativa) no valor adicionado", "66,4% (2013); 40,8% (2020)", "PIB dos Municípios (tab. 5938)"),
 ("Participação da agropecuária no valor adicionado (2021)", "1,0%", "PIB dos Municípios (tab. 5938)"),
 ("Cana-de-açúcar: quantidade produzida", "4,28 mi t (2005); 1,29 mi t (2023)", "PAM (tab. 1612)"),
]
tab = d.add_table(rows=0, cols=3); tab.style = "Table Grid"
for i, row in enumerate(t1):
    cells = tab.add_row().cells
    for j, v in enumerate(row):
        cells[j].text = v
        for r_ in cells[j].paragraphs[0].runs:
            r_.font.size = Pt(8.5); r_.bold = (i == 0)
p_txt("Fonte: elaboração própria a partir de IBGE (2026); valores correntes, sem deflacionamento; interpretação histórica conforme "
      "Silva e Hasenclever (2019).", indent=False, size=8.5, after=4)

# ---------- Figura 1 ----------
pf = d.add_paragraph(); pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
pf.add_run().add_picture("saidas/figuras/F1_cat_ano_categorias.png", width=Cm(14.5))
p_txt("Figura 1 – CATs de profissões da saúde (universo principal, n = 1.144) vinculadas a empregadores de Campos dos Goytacazes (RJ), por ano "
      "do acidente e categoria profissional, 2018–2025. Unidade: registros. Fonte: elaboração própria a partir de BRASIL (2026a). "
      "*Cobertura parcial/irregular da fonte (2018: competências desde jul.; 2022: carga irregular; 2024: set.–dez. atípicos; 2025: até out.). "
      "Frequências de comunicação, não taxas de acidente.", indent=False, size=8.5, after=4)

# ---------- Figura 2 ----------
pf2 = d.add_paragraph(); pf2.alignment = WD_ALIGN_PARAGRAPH.CENTER
pf2.add_run().add_picture("saidas/figuras/F2_serie_mensal_saude.png", width=Cm(14.5))
p_txt("Figura 2 – Distribuição mensal das CATs de profissões da saúde (universo principal, n = 1.144), empregadores de Campos dos "
      "Goytacazes (RJ), jan./2018–dez./2025, com destaque para o período crítico da covid-19 (mar./2020–dez./2021). Unidade: registros/mês. "
      "Fonte: elaboração própria a partir de BRASIL (2026a). As oscilações também refletem a cobertura da fonte (ver notas da Figura 1); "
      "médias mensais: 10,7 (pré-pandemia), 14,5 (período crítico) e 11,9 (pós-crítico).", indent=False, size=8.5, after=4)

# ---------- Tabela 2 ----------
p_txt("Tabela 2 – Características das CATs das profissões da saúde, empregadores de Campos dos Goytacazes (RJ), 2018–2025 (n = 1.144)",
      indent=False, size=9.5, bold=True, after=2)
t2 = [
 ("Característica", "n (%)"),
 ("Enfermagem – técnicos e auxiliares", "803 (70,2)"),
 ("Enfermagem – enfermeiros", "163 (14,2)"),
 ("Diagnóstico e laboratório – técnicos e auxiliares", "78 (6,8)"),
 ("Fisioterapia", "30 (2,6)"),
 ("Farmácia – técnicos e auxiliares", "20 (1,7)"),
 ("Agentes comunitários de saúde e afins", "14 (1,2)"),
 ("Medicina", "12 (1,0)"),
 ("Demais categorias (farmácia, nutrição, odontologia/saúde bucal, fonoaudiologia, instrumentação; n<5 agregados)", "24 (2,1)"),
 ("Sexo feminino", "980 (85,7)"),
 ("Acidente típico | trajeto | doença", "937 (81,9) | 196 (17,1) | 11 (1,0)"),
 ("Parte atingida: dedo", "502 (43,9)"),
 ("Agente causador biológico/infeccioso", "308 (26,9)"),
 ("CID-10: S61 (ferimento punho/mão) | Z20 (exposição a doenças transmissíveis)", "287 (25,1) | 250 (21,9)"),
 ("Empregador em CNAE 86/87 (dos quais classe 8610 – hospitalar)", "1.091 (95,4) | 879 (76,8)"),
 ("CAT emitida pelo empregador; mediana acidente→emissão = 1 dia", "1.110 (97,0)"),
]
tab2 = d.add_table(rows=0, cols=2); tab2.style = "Table Grid"
for i, row in enumerate(t2):
    cells = tab2.add_row().cells
    for j, v in enumerate(row):
        cells[j].text = v
        for r_ in cells[j].paragraphs[0].runs:
            r_.font.size = Pt(8.5); r_.bold = (i == 0)
p_txt("Fonte: elaboração própria a partir de BRASIL (2026a). Idade mediana: 36 anos. Percentuais sobre o total de registros do universo "
      "principal; sexo ignorado em 4 registros; um óbito registrado.", indent=False, size=8.5, after=6)

# ---------- Referências ----------
p_txt("Referências", indent=False, bold=True, size=10.5, before=2, after=2)
refs = [
 "ANTUNES, R. O privilégio da servidão: o novo proletariado de serviços na era digital. São Paulo: Boitempo, 2018.",
 "BRASIL. Instituto Nacional do Seguro Social. Comunicações de Acidente de Trabalho – CAT: dados abertos, competências jul. 2018–dez. 2025. "
 "Brasília, DF: INSS, 2026a. Disponível em: https://dados.gov.br/dados/conjuntos-dados/inss-comunicacao-de-acidente-de-trabalho-cat. Acesso em: 18 jul. 2026.",
 "BRASIL. Ministério da Saúde. DATASUS. CNES – Recursos Humanos – Profissionais – Indivíduos – segundo CBO 2002 – Rio de Janeiro. "
 "Brasília, DF: Ministério da Saúde, 2026b. TabNet. Disponível em: http://tabnet.datasus.gov.br. Acesso em: 18 jul. 2026.",
 "CECILIO, L. C. O.; LACAZ, F. A. C. O trabalho em saúde. Rio de Janeiro: Cebes, 2012.",
 "IBGE. Sistema IBGE de Recuperação Automática – SIDRA: Censo Demográfico 2022 (tabela 4714); Produto Interno Bruto dos Municípios (tabela 5938); "
 "Produção Agrícola Municipal (tabela 1612). Rio de Janeiro: IBGE, 2026. Acesso em: 18 jul. 2026.",
 "LEMOS, M. R. Estratificação social na teoria de Max Weber: considerações em torno do tema. Revista Iluminart, Sertãozinho, ano 4, n. 9, "
 "p. 113-128, nov. 2012.",
 "LOURENÇO, G. G. O fim do fim do trabalho: uma crítica à chamada sociedade pós-industrial e sua relação com os movimentos de trabalhadores. "
 "Primeiros Estudos, São Paulo, n. 3, p. 104-121, 2012.",
 "MARTINS, S.; HASENCLEVER, L.; MIRANDA, C. A gestão da saúde à luz da instabilidade de financiamento e das propostas de governo. "
 "Cadernos do Desenvolvimento Fluminense, Rio de Janeiro, n. 27, 2024. DOI: 10.12957/cdf.2024.87352.",
 "MENDES, R.; DIAS, E. C. Da medicina do trabalho à saúde do trabalhador. Revista de Saúde Pública, São Paulo, v. 25, n. 5, p. 341-349, 1991. "
 "DOI: 10.1590/S0034-89101991000500003.",
 "OLIVEIRA, E. M. Transformações no mundo do trabalho, da Revolução Industrial aos nossos dias. Caminhos de Geografia, Uberlândia, v. 6, n. 11, "
 "p. 84-96, fev. 2004.",
 "SILVA, J. E. M. da; HASENCLEVER, L. Ciclo do petróleo e desenvolvimento socioeconômico no município de Campos dos Goytacazes – 1999/2014. "
 "Desenvolvimento em Questão, Ijuí, v. 17, n. 46, p. 314-332, 2019. DOI: 10.21527/2237-6453.2019.46.314-332.",
 "VEDOVATO, T. G.; ANDRADE, C. B.; SANTOS, D. L.; BITENCOURT, S. M.; ALMEIDA, L. P. de; SAMPAIO, J. F. da S. Trabalhadores(as) da saúde e a "
 "COVID-19: condições de trabalho à deriva? Revista Brasileira de Saúde Ocupacional, São Paulo, v. 46, e1, 2021. DOI: 10.1590/2317-6369000028520.",
]
for r_ in refs:
    p_txt(r_, indent=False, just=False, size=9.5, after=2)

os.makedirs("documentos", exist_ok=True)
d.save("documentos/artigo.docx")

# ---------- verificação de páginas (multiplataforma) ----------
import shutil
soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
if os.path.exists(soffice):
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", "documentos", "documentos/artigo.docx"],
                   capture_output=True, timeout=300)
    from pypdf import PdfReader
    npag = len(PdfReader("documentos/artigo.pdf").pages)
    print(f"artigo.docx gerado — PDF de verificação com {npag} página(s).")
    if npag > 5:
        raise SystemExit("LIMITE EXCEDIDO: artigo com mais de 5 páginas — revisar conteúdo.")
else:
    print("AVISO: LibreOffice ausente — número de páginas NÃO verificado nesta máquina.")
