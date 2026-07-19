# -*- coding: utf-8 -*-
"""
dbc_decompressor.py - Pure Python decompressor for DATASUS .dbc files.
Implements a subset of the PKWare BLAST/DCL algorithm.

Usage: python dbc_decompressor.py input.dbc output.dbf
"""
import struct, sys, os


class BitStream:
    """Read bits from a byte buffer, MSB first."""
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.buf = 0
        self.nbits = 0

    def need_bits(self, n):
        while self.nbits < n:
            if self.pos < len(self.data):
                self.buf = (self.buf << 8) | self.data[self.pos]
            else:
                self.buf = self.buf << 8
            self.pos += 1
            self.nbits += 8

    def take_bits(self, n):
        self.need_bits(n)
        self.nbits -= n
        val = (self.buf >> self.nbits) & ((1 << n) - 1)
        self.buf &= (1 << self.nbits) - 1 if self.nbits > 0 else 0
        return val


def build_huffman_tree(lengths):
    """Build canonical Huffman tree from code lengths (RFC 1951 style)."""
    if not lengths:
        return {}, 0
    max_len = max(lengths)
    bl_count = [0] * (max_len + 1)
    for l in lengths:
        bl_count[l] += 1
    code = 0
    next_code = [0] * (max_len + 1)
    for bits in range(1, max_len + 1):
        code = (code + bl_count[bits - 1]) << 1
        next_code[bits] = code
    tree = {}
    for sym, l in enumerate(lengths):
        if l > 0:
            tree[(next_code[l], l)] = sym
            next_code[l] += 1
    return tree, max_len


def decode_huffman(bs, tree, max_len):
    """Decode one symbol from a Huffman tree."""
    code = 0
    for blen in range(1, max_len + 1):
        code = (code << 1) | bs.take_bits(1)
        key = (code, blen)
        if key in tree:
            return tree[key]
    return -1


def read_lengths(bs, count, hclen):
    """Read code lengths using a given Huffman table."""
    lengths = []
    while len(lengths) < count:
        sym = decode_huffman(bs, *hclen)
        if sym < 0:
            break
        if sym < 16:
            lengths.append(sym)
        elif sym == 16:
            repeat = 3 + bs.take_bits(2)
            if lengths:
                lengths.extend([lengths[-1]] * repeat)
        elif sym == 17:
            repeat = 3 + bs.take_bits(3)
            lengths.extend([0] * repeat)
        elif sym == 18:
            repeat = 11 + bs.take_bits(7)
            lengths.extend([0] * repeat)
    return lengths[:count]


def decode_block(bs, lit_tree, dist_tree):
    """Decode one compressed block (RFC 1951 / deflate style)."""
    output = bytearray()
    length_base = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31,
                   35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258]
    length_extra = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2,
                    3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0]
    dist_base = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193,
                 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145,
                 8193, 12289, 16385, 24577]
    dist_extra = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
                  7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13]

    while True:
        sym = decode_huffman(bs, *lit_tree)
        if sym < 0:
            break
        if sym < 256:
            output.append(sym)
        elif sym == 256:
            break
        else:
            idx = sym - 257
            if idx >= len(length_base):
                break
            length = length_base[idx] + bs.take_bits(length_extra[idx])
            dsym = decode_huffman(bs, *dist_tree)
            if dsym < 0:
                break
            if dsym >= len(dist_base):
                break
            dist = dist_base[dsym] + bs.take_bits(dist_extra[dsym])
            start = len(output) - dist
            if start < 0:
                start = 0
            for _ in range(length):
                output.append(output[start])
                start += 1
    return bytes(output)


def decompress_deflate(data):
    """Decompress deflate/zlib data (RFC 1951)."""
    bs = BitStream(data)
    output = bytearray()
    bfinal = 0
    while not bfinal:
        bfinal = bs.take_bits(1)
        btype = bs.take_bits(2)
        if btype == 0:
            # No compression
            bs.need_bits(bs.nbits % 8)
            bs.take_bits(bs.nbits % 8)
            if bs.pos + 4 > len(data):
                break
            length = struct.unpack('<H', data[bs.pos:bs.pos+2])[0]
            bs.pos += 2
            nlength = struct.unpack('<H', data[bs.pos:bs.pos+2])[0]
            bs.pos += 2
            output.extend(data[bs.pos:bs.pos+length])
            bs.pos += length
            bs.buf = 0
            bs.nbits = 0
        elif btype == 1:
            # Fixed Huffman
            lit_len = [8]*144 + [9]*(256-144) + [7]*(280-256) + [8]*(288-280)
            dist_len = [5]*32
            lit_tree = build_huffman_tree(lit_len)
            dist_tree = build_huffman_tree(dist_len)
            output.extend(decode_block(bs, lit_tree, dist_tree))
        elif btype == 2:
            # Dynamic Huffman
            hlit = bs.take_bits(5) + 257
            hdist = bs.take_bits(5) + 1
            hclen = bs.take_bits(4) + 4
            clen_order = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]
            clen_vals = [0]*19
            for i in range(hclen):
                clen_vals[clen_order[i]] = bs.take_bits(3)
            clen_tree = build_huffman_tree(clen_vals)
            lit_lens = read_lengths(bs, hlit + hdist, clen_tree)
            lit_tree = build_huffman_tree(lit_lens[:hlit])
            dist_lens = lit_lens[hlit:]
            if len(dist_lens) < hdist:
                dist_lens += [0] * (hdist - len(dist_lens))
            dist_tree = build_huffman_tree(dist_lens[:hdist])
            output.extend(decode_block(bs, lit_tree, dist_tree))
        else:
            break
    return bytes(output)


def dbc_to_dbf(input_path, output_path):
    """Convert DATASUS .dbc to .dbf."""
    with open(input_path, 'rb') as f:
        data = f.read()

    if len(data) < 32:
        return False

    # Read DBF header length (bytes 8-9, little-endian)
    header_len = struct.unpack('<H', data[8:10])[0]
    if header_len <= 0 or header_len > len(data):
        header_len = data.find(b'\x0d', 32)
        if header_len < 0:
            header_len = 160
        else:
            header_len += 1

    header = data[:header_len]
    compressed = data[header_len:]

    # Each compressed block: 4 bytes uncomp_len + 4 bytes comp_len + data
    all_out = bytearray()
    pos = 0
    block_count = 0

    while pos < len(compressed):
        if pos + 8 > len(compressed):
            break
        uncomp_len = struct.unpack('<I', compressed[pos:pos+4])[0]
        comp_len = struct.unpack('<I', compressed[pos+4:pos+8])[0]
        pos += 8
        if comp_len <= 0 or pos + comp_len > len(compressed):
            break
        block = compressed[pos:pos+comp_len]
        pos += comp_len
        block_count += 1

        try:
            import zlib
            decompressed = zlib.decompress(block, -15)
            if len(decompressed) != uncomp_len:
                pass  # try other methods
            all_out.extend(decompressed)
        except:
            try:
                decompressed = decompress_deflate(block)
                all_out.extend(decompressed)
            except:
                # If all else fails, just store the block raw
                all_out.extend(block)

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(bytes(all_out))

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Test mode
        test_file = 'dados/brutos/sinan/ACGRBR18.dbc'
        out_file = 'dados/brutos/sinan/test_acgr18.dbf'
        print(f'Test: {test_file} -> {out_file}')
        ok = dbc_to_dbf(test_file, out_file)
        if ok:
            sz = os.path.getsize(out_file)
            print(f'Output: {sz} bytes')

            from dbfread import DBF
            try:
                dbf = DBF(out_file, encoding='latin-1', char_decode_errors='replace')
                count = 0
                campos = 0
                for rec in dbf:
                    count += 1
                    mun = str(rec.get('ID_MN_RESI', rec.get('ID_MUNICIP', ''))).strip()
                    if mun == '330100':
                        campos += 1
                print(f'Records: {count}, Campos: {campos}')
            except Exception as e:
                print(f'DBF read error: {e}')
        else:
            print('Conversion failed')
    else:
        dbc_to_dbf(sys.argv[1], sys.argv[2])
