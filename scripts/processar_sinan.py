# -*- coding: utf-8 -*-
"""
processar_sinan.py
==================
Leitor customizado dos arquivos DBF do SINAN (DATASUS).
Os DBFs do SINAN tem um registro de cabecalho com flag 'H' que quebra
o dbfread e simpledbf. Este script le o DBF binario diretamente.

Filtra: Campos dos Goytacazes (330100) | 2018-2025
"""
import os, csv, struct, sys
from collections import defaultdict

MUN_COD = "330100"
DIR_SINAN = os.path.join("dados", "brutos", "sinan")
DIR_PROC = os.path.join("dados", "processados")
DIR_SAIDAS = os.path.join("saidas", "tabelas")
os.makedirs(DIR_PROC, exist_ok=True)
os.makedirs(DIR_SAIDAS, exist_ok=True)

AGRAVOS = {
    "ACGR": "Acidente de Trabalho Grave",
    "ACBI": "Acid Trab Exposicao Material Biologico",
    "ANIM": "Acidente por Animais Peconhentos",
    "CANC": "Cancer Relacionado ao Trabalho",
    "DERM": "Dermatose Relacionada ao Trabalho",
    "LERD": "LER/DORT",
    "MENT": "Transtorno Mental Relacionado ao Trabalho",
    "PAIR": "PAIR Relacionado ao Trabalho",
    "PNEU": "Pneumoconiose Relacionada ao Trabalho",
}


def ler_dbf_fields(f, header_len):
    """Le os descritores de campo do DBF."""
    n_fields = (header_len - 33) // 32
    f.seek(32)
    fields = []
    for _ in range(n_fields):
        data = f.read(32)
        name = data[0:11].split(b"\x00")[0].decode("ascii", errors="replace")
        ftype = chr(data[11])
        flen = data[16]
        fdec = data[17]
        fields.append((name, ftype, flen, fdec))
    return fields


def ler_registro(f, offset, fields, rec_len):
    """Le um registro na posicao offset e retorna dicionario."""
    f.seek(offset)
    rec = f.read(rec_len)

    # Flag: ' ' = valido, '*' = deletado, 'H' = header interno
    flag = chr(rec[0])

    valores = {}
    pos = 1
    for name, ftype, flen, fdec in fields:
        raw = rec[pos : pos + flen]
        if ftype in ("C", "D", "L", "M"):
            val = raw.decode("latin-1", errors="replace").strip()
        elif ftype == "N":
            s = raw.strip()
            val = s.decode("ascii", errors="replace").strip()
        elif ftype == "F":
            s = raw.decode("ascii", errors="replace").strip()
            try:
                val = float(s) if s else 0.0
            except ValueError:
                val = s
        else:
            val = raw.decode("latin-1", errors="replace").strip()
        valores[name] = val
        pos += flen

    return flag, valores


def processar_arquivo(path, agravo_cod, agravo_nome, ano):
    """Le um arquivo DBF e extrai registros de Campos."""
    registros = []
    try:
        with open(path, "rb") as f:
            # Header DBF
            f.seek(0)
            ver = f.read(1)[0]
            if ver != 3 and ver != 0x30:
                print(f"    Versao DBF desconhecida: {ver}, pulando.")
                return registros

            yy, mm, dd = struct.unpack("BBB", f.read(3))
            n_records = struct.unpack("<I", f.read(4))[0]
            header_len = struct.unpack("<H", f.read(2))[0]
            rec_len = struct.unpack("<H", f.read(2))[0]

            fields = ler_dbf_fields(f, header_len)

            # Encontrar coluna de municipio
            mun_field = None
            for name, _, _, _ in fields:
                upper = name.upper()
                if "ID_MUNICIP" in upper or "MUNICIP" in upper:
                    if "IBGE" not in upper and "EMP" not in upper:
                        mun_field = name
                        break
            if not mun_field:
                # Tentar qualquer coluna com MUN
                for name, _, _, _ in fields:
                    if "MUN" in name.upper():
                        mun_field = name
                        break

            if not mun_field:
                print(f"    Coluna municipio nao encontrada. Campos: {[n for n,_,_,_ in fields[:15]]}")
                return registros

            # Ler registros
            data_start = header_len
            n_validos = 0
            n_campos = 0

            for rec_idx in range(n_records):
                offset = data_start + rec_idx * rec_len
                flag, valores = ler_registro(f, offset, fields, rec_len)

                if flag == " ":  # Registro valido
                    n_validos += 1
                    mun = str(valores.get(mun_field, "")).strip()
                    if mun == MUN_COD:
                        n_campos += 1
                        # Selecionar campos relevantes
                        rec_clean = {
                            "_agravo_cod": agravo_cod,
                            "_agravo_nome": agravo_nome,
                            "_ano": ano,
                            "_arquivo": os.path.basename(path),
                        }
                        # Copiar todos os campos
                        for name, val in valores.items():
                            rec_clean[name] = str(val) if val is not None else ""
                        registros.append(rec_clean)

            if n_campos > 0:
                print(f"    Registros validos: {n_validos}/{n_records} | Campos: {n_campos}")

    except Exception as e:
        print(f"    ERRO: {type(e).__name__}: {e}")

    return registros


def main():
    print("=" * 70)
    print("PROCESSAMENTO SINAN - CAMPOS DOS GOYTACAZES (330100)")
    print("2018-2025 | 9 agravos de notificacao relacionados ao trabalho")
    print("=" * 70)

    todos_registros = []
    estatisticas = defaultdict(lambda: defaultdict(int))

    arquivos = sorted(os.listdir(DIR_SINAN))
    dbcs = [f for f in arquivos if f.upper().endswith(".DBC")]

    print(f"\n{len(dbcs)} arquivos .dbc encontrados em {DIR_SINAN}")

    for nome in dbcs:
        prefixo = nome[:4].upper()
        if prefixo not in AGRAVOS:
            continue

        # Extrair ano
        try:
            ano_suf = int(nome[6:8])
            ano = 2000 + ano_suf if ano_suf < 60 else 1900 + ano_suf
        except:
            continue

        if ano < 2018 or ano > 2025:
            continue

        agravo_nome = AGRAVOS[prefixo]
        path = os.path.join(DIR_SINAN, nome)

        print(f"\n  [{prefixo}] {ano} ({nome})")
        regs = processar_arquivo(path, prefixo, agravo_nome, ano)
        todos_registros.extend(regs)
        estatisticas[prefixo][ano] = len(regs)

    # ========== SALVAR ==========
    if todos_registros:
        # Coletar todas as colunas
        all_cols = set()
        for r in todos_registros:
            all_cols.update(r.keys())

        # Ordenar: _meta primeiro, depois alfabetico
        meta_cols = sorted([c for c in all_cols if c.startswith("_")])
        data_cols = sorted([c for c in all_cols if not c.startswith("_")])
        colunas = meta_cols + data_cols

        path = os.path.join(DIR_PROC, "sinan_campos_2018_2025.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=colunas, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(todos_registros)

        mb = os.path.getsize(path) / 1e6
        print(f"\n{'='*70}")
        print(f"CSV salvo: {path} ({mb:.1f} MB, {len(todos_registros)} registros)")
    else:
        print("\nNENHUM registro de Campos encontrado.")

    # ========== RESUMO ==========
    print(f"\n{'='*70}")
    print("RESUMO SINAN - Campos dos Goytacazes 2018-2025")
    print(f"{'='*70}")
    header_anos = " ".join(f"{a:>5}" for a in range(2018, 2026))
    print(f"{'Agravo':<47} {header_anos} {'Total':>6}")
    print("-" * 85)

    total_geral = 0
    for cod, nome in sorted(AGRAVOS.items(), key=lambda x: x[1]):
        total_agravo = 0
        row = f"  {nome[:45]:<45}"
        for ano in range(2018, 2026):
            n = estatisticas[cod].get(ano, 0)
            row += f" {n:>5}"
            total_agravo += n
            total_geral += n
        row += f" {total_agravo:>6}"
        print(row)

    print("-" * 85)
    print(f"  {'TOTAL':<45}", end="")
    for ano in range(2018, 2026):
        s = sum(estatisticas[ag].get(ano, 0) for ag in AGRAVOS)
        print(f" {s:>5}", end="")
    print(f" {total_geral:>6}")

    # Tabela resumo
    t39_path = os.path.join(DIR_SAIDAS, "T39_sinan_resumo_agravo_ano.csv")
    with open(t39_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["agravo"] + [str(a) for a in range(2018, 2026)] + ["total"])
        for cod, nome in sorted(AGRAVOS.items(), key=lambda x: x[1]):
            row = [nome]
            total = 0
            for ano in range(2018, 2026):
                n = estatisticas[cod].get(ano, 0)
                row.append(n)
                total += n
            row.append(total)
            writer.writerow(row)

    print(f"\nTabela resumo: {t39_path}")


if __name__ == "__main__":
    main()
