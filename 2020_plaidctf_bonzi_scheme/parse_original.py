import bitstring

BO = 'little'

def ifb(data):
    return int.from_bytes(data, BO)

class Guid(): # 16 bytes
    def __init__(self, data, offset):
        pass

    def total_len(self):
        return 16

class ACSString():
    def __init__(self, _data, offset):
        data = _data[offset:]
        self.len = ifb(data[:4])
        #print(f"DEBUG: strlen {self.len}")

        self.str = ""

        for i in range(self.len):
            b = data[4+i*2:6+i*2]
            self.str += chr(ifb(b))

        print(self.len, self.str)

    def total_len(self):
        return 4 + self.len*2

class ACSVoiceInfo(): # 39 bytes: 2*16+4+2+1
    def __init__(self, _data, offset):
        orig_offset = offset
        data = _data[offset:]
        self.extra_data_present = bool(data[38])
        if self.extra_data_present:
            data = data[39:]
            # 2 bytes langid: ushort
            self.langid = ifb(data[:2])
            # 4 bytes strlen
            self.language_dialect = ACSString(data, 2)
            offset = 2 + self.language_dialect.total_len()
            #print(offset)
            data = data[offset:]
            self.gender = ifb(data[:2])
            self.age = ifb(data[2:4])
            self.style = ACSString(data, 4)
            offset = 4 + self.style.total_len()
            data = data[offset:]
            #print(offset)

    def total_len(self):
        size = 39
        if self.extra_data_present:
            size += 6
            size += self.language_dialect.total_len()
            size += self.style.total_len()
        return size

class RGBQuad():
    def __init__(self, _data, offset):
        data = _data[offset:]
        self.r = data[0]
        self.g = data[1]
        self.b = data[2]
        #print(self.r, self.g, self.b, data[3])
        assert data[3] == 0

    def total_len(self):
        return 4

class ACSBalloonInfo():
    def __init__(self, _data, offset):
        data = _data[offset:]
        self.num_text_lines = data[0]
        self.chars_per_line = data[1]
        #print(f"self.num_text_lines: {self.num_text_lines}, self.chars_per_line: {self.chars_per_line}")
        self.foreground_color = RGBQuad(data, 2)
        self.background_color = RGBQuad(data, 6)
        self.border_color = RGBQuad(data, 10)
        #print(self.num_text_lines, self.chars_per_line)

        self.font_name = ACSString(data, 14)
        data = data[14+self.font_name.total_len():]
        #print(data)
        self.font_height = ifb(data[:4])
        self.font_weight = ifb(data[6:8]) # idk why 6:8
        #print(self.font_height, self.font_weight)
        self.italic = data[8]
        self.unknown = data[9]
        #print(self.italic, self.unknown)

    def total_len(self):
        return 14 + self.font_name.total_len() + 10

class ACSLocator():
    def __init__(self, data, offset):
        _data = data[offset:]
        self.offset = int.from_bytes(_data[:4], BO)
        self.size = int.from_bytes(_data[4:8], BO)

    def total_len(self):
        return 8

class ACSHeader():
    def __init__(self, data, offset):
        _data = data[offset:]
        assert _data[:4] == b'\xc3\xab\xcd\xab'
        self.loc_acscharacter = ACSLocator(data, 4)
        self.loc_acsanimation = ACSLocator(data, 12)
        self.loc_acsimage = ACSLocator(data, 20)
        print("locasimageoffset: ", self.loc_acsimage.offset, self.loc_acsimage.size)
        self.loc_acsaudio = ACSLocator(data, 28)

class ACSList():
    def __init__(self, _data, offset, countsize, Type):
        orig_offset = offset
        data = _data[offset:]
        #print(data)
        if Type == RGBQuad:
            count = int.from_bytes(data[1:countsize+1], 'big') # this doesn't make any sense, but it works :D
            data = data[countsize+2:] # this doesn't make any sense, but it works :D
        else:
            count = int.from_bytes(data[:countsize], 'little')
            data = data[countsize:]
        self.elems = []
        offset = 0
        for i in range(count):
            #if Type == RGBQuad:
                #print(f"list_offset: {offset + orig_offset}")
            new_elem = Type(data, offset)
            offset += new_elem.total_len()
            self.elems.append(new_elem)

    def total_len(self):
        out = 4
        for e in self.elems:
            out += e.total_len()
        return out

class ACSPaletteColor():
    def __init__(self, _data, offset):
        data = _data[offset:]
        self.rgbquad = RGBQuad(data, 0)

class ACSImageInfo():
    def __init__(self, _data, offset):
        data = _data[offset:]
        self.loc = ACSLocator(data, 0)
        self.checksum = ifb(data[8:12])

    def total_len(self):
        return 12

"""def bitstream_to_byte(b):
    '''#assert len(b) == 8
    #print(b, len(b))

    out = 0
    for i in range(len(b))[::-1]:
        out <<= 1
        out |= b[i]
    return out'''
    return int(''.join(["%s" % x for x in b[::-1]]), 2)

def byte_to_bitstream(b):
    out = []
    for i in range(8):
        out.append(b & 1)
        b >>= 1
    return out

def bytes_to_bitstream(data):
    out = []
    for b in data:
        out += byte_to_bitstream(b)
    return out"""

def bytes_to_bitstream(data_bytes):
    data_bitstream = bitstring.BitArray(data_bytes)
    for i in range(0, len(data_bitstream), 8):
        data_bitstream.reverse(i, i+8)
    return data_bitstream

def bitstream_to_bytes(data_bitstream, offset, length):
    data_bytes = data_bitstream[offset:offset+length]
    for i in range(0, len(data_bytes), 8):
        data_bytes.reverse(i, min(len(data_bytes), i+8))
    if len(data_bytes) % 8 != 0:
        data_bytes.prepend("0b" + "0"*(8-(len(data_bytes) % 8)))
    return data_bytes.bytes

def bitstream_to_value(data_bitstream, offset, length):
    data_bytes = data_bitstream[offset:offset+length]
    data_bytes.reverse()
    if len(data_bytes) % 8 != 0:
        data_bytes.prepend("0b" + "0"*(8-(len(data_bytes) % 8)))
    return int(data_bytes.hex, 16)

def decompress(data):
    assert data[0] == 0
    assert data[-6:] == b'\xff'*6

    out = [0] * 200*160*30
    print(out[:100])

    #compressed_data = data[1:-6]
    compressed_data = data[1:]
    print(compressed_data)
    bs = bytes_to_bitstream(compressed_data)
    #print(bs)
    pointer = 0
    while bs:
        if bs[0] == 0:
            byte = bitstream_to_value(bs, 1, 8)
            bs = bs[9:]
            #print(f"uncompressed_byte: {byte}")
            out[pointer] = byte
            print(byte)
            pointer += 1
        else:
            bytes_to_decode = 2
            bit_count = None
            print(bs[:20])
            if bs[1] == 0:
                bit_count = 6
                bs = bs[2:]
            elif bs[2] == 0:
                bit_count = 9
                bs = bs[2:]
            elif bs[3] == 0:
                bit_count = 12
                bs = bs[3:]
            else:
                #bytes_to_decode += 1 # ?????
                bit_count = 20
                bs = bs[3:] # this must be 3: and not 4:
                print(bs[:12])
            if bit_count is None:
                raise Exception("bit_count is None")
            print(f"bit_count: {bit_count}, bits: {bs[:bit_count]}")
            num = bitstream_to_value(bs, 0, bit_count)
            print(num)
            print(f"num: {num}")
            if bit_count == 20 and num == 0x000FFFFF:
                print(f"Reached EOF, pointer: {pointer}")
                return out[:pointer]
            if bit_count == 6:
                num += 1
            if bit_count == 9:
                num += 65
            if bit_count == 12:
                num += 577
            if bit_count == 20:
                num += 4673
            offset = num
            if offset > 0xfffff:
                raise Exception("huh?")
            #print(f"offset_bit_count: {bit_count}")
            bs = bs[bit_count:]
            one_bit_count = 0
            for i in range(12):
                if i == 11 and bs[i] == 1:
                    raise Exception("Error occured")
                if bs[i] == 1:
                    one_bit_count += 1
                else:
                    break
            print(f"offset: {offset}")
            #print(f"one_bit_count: {one_bit_count}")
            if one_bit_count > 0:
                numeric_value = bitstream_to_value(bs, 0, one_bit_count+1)
                #print(f"numeric_value: {numeric_value}")
                bytes_to_decode += numeric_value
                bs = bs[one_bit_count+1:]
                numeric_value = bitstream_to_value(bs, 0, one_bit_count)
                bs = bs[one_bit_count:]
                #print(f"numeric_value: {numeric_value}")
                bytes_to_decode += numeric_value
            else:
                bs = bs[1:]
            print(f"bytes_to_decode: {bytes_to_decode}")
            curr_offset = pointer - offset
            print(f"pointer: {pointer}")
            #print(offset)
            #print(curr_offset)
            for i in range(bytes_to_decode):
                #print(f"Copying: {out[curr_offset]}")

                out[pointer] = out[max(curr_offset,0)]
                pointer += 1
                curr_offset += 1
        #print(pointer)
    return out

class Datablock():
    def __init__(self, _data, offset):
        data = _data[offset:]
        self.size = ifb(data[:4])
        self.content = data[4:4+self.size]

    def total_len(self):
        return self.size + 4

class ACSImage():
    def __init__(self, _data, offset):
        orig_offset = offset
        data = _data[offset:]
        self.unknown = data[0]
        print(f"Image orig_offset: {orig_offset}")
        self.width = ifb(data[1:3])
        self.height = ifb(data[3:5])
        self.compression_flag = data[5]

        print(self.width, self.height)

        if not self.compression_flag:
            print(self.width, self.height, self.compression_flag)

        self.image_data = Datablock(data, 6)

        abc = bytearray(self.image_data.content)
        print("aaaaaaaaaa", _data[orig_offset + 4 + 6 + 1])
        abc[1] = 0x02
        print(self.image_data.content[:5])
        self.image_data.content = bytes(abc)
        print(self.image_data.content[:5])
        return
        decompressed = decompress(self.image_data.content)
        print(len(decompressed))
        print(decompressed[:100])
        self.image_data_size = ifb(decompressed[:4])

        return

        data = data[6+self.image_data.total_len():]
        self.compressed_region_data_size = ifb(data[:4])
        self.uncompressed_region_data_size = ifb(data[4:8])
        #print(self.compressed_region_data_size, self.uncompressed_region_data_size)
        data = data[8:]
        self.region_data_raw = decompress(data[:self.compressed_region_data_size])

class ACSCharacterInfo():
    def __init__(self, _data, offset):
        orig_offset = offset
        data = _data[offset:]
        self.minor_version = ifb(data[0:2])
        self.major_version = ifb(data[2:4])
        self.loc_localizedinfo = ACSLocator(_data, orig_offset + 4)
        print("self.loc_localizefindo pos: ", orig_offset + 4)
        print("stuff", self.loc_localizedinfo.offset, self.loc_localizedinfo.size)
        print(_data[self.loc_localizedinfo.offset:self.loc_localizedinfo.offset+4])
        print(self.loc_localizedinfo.size)
        #print(data[self.loc_localizedinfo.offset])
        #self.localized_info = ACSString(_data, self.loc_localizedinfo.offset)
        self.guid = Guid(data, 12)
        self.width = ifb(data[28:30])
        self.height = ifb(data[30:32])
        #print(self.width, self.height)
        self.transparent_color_index = data[32]
        self.idx_transparent = self.transparent_color_index
        #print(f"self.idx_transparent: {self.idx_transparent}")
        self.flags = ifb(data[33:37])
        self.animation_set_major_version = ifb(data[37:39])
        self.animation_set_minor_version = ifb(data[39:41])
        #print(f"animation set major/minor: {self.animation_set_major_version}.{self.animation_set_minor_version}")
        self.voiceinfo = ACSVoiceInfo(data, 41)
        offset = 41 + self.voiceinfo.total_len()
        offset += 2 # idk why
        self.ballooninfo = ACSBalloonInfo(data, offset)
        offset += self.ballooninfo.total_len()
        self.palette_offset = offset + orig_offset
        self.palette = ACSList(_data, orig_offset+offset, 4, RGBQuad)
        offset += self.palette.total_len()
        offset += 2
        self.system_tray_icon_flag = data[offset]
        #print(self.system_tray_icon_flag)
        # TODO: parse the rest of this if you need it


def parse(data):
    header = ACSHeader(data, 0)
    print(f"File size: {len(data)}")
    print(f"ACSCharacterInfo pointer: {ifb(data[4:8])}")
    print(f"ACSCharacterInfo size: {ifb(data[8:12])}")
    print(f"ACSAnimationInfo pointer: {ifb(data[12:16])}")
    print(f"ACSAnimationInfo size: {ifb(data[16:20])}")
    print(f"ACSImageInfo pointer: {ifb(data[20:24])}")
    print(f"ACSImageInfo size: {ifb(data[24:28])}")
    print(f"ACSAudioInfo pointer: {ifb(data[28:32])}")
    print(f"ACSAudioInfo size: {ifb(data[32:36])}")

    image_infos = ACSList(data, header.loc_acsimage.offset, 4, ACSImageInfo)
    print(f"Image count: {len(image_infos.elems)}")
    print(f"First image pos: {ifb(data[header.loc_acsimage.offset+4:header.loc_acsimage.offset+8])}")
    print(f"Last image pos: {ifb(data[header.loc_acsimage.offset-8+12*len(image_infos.elems):header.loc_acsimage.offset-4+12*len(image_infos.elems)])}")

    character = ACSCharacterInfo(data, header.loc_acscharacter.offset)
    print(f"Location of localized_info: {character.loc_localizedinfo.offset}")
    print(f"Size of localized_info: {character.loc_localizedinfo.size}")

    last_image = ACSImage(data, image_infos.elems[-1].loc.offset)
    print(f"Last image width:  {last_image.width}")
    print(f"Last image height: {last_image.height}")
    print(f"Last image compression flag: {last_image.compression_flag}")
    print(f"Last image datablock length: {last_image.image_data.size}")

    print(len(data))
    abc = bytearray(data)
    orig_pointer = int.from_bytes(data[20:24], BO)
    list_len = data[orig_pointer:orig_pointer+4]
    abc[20:24] = len(data).to_bytes(4, byteorder=BO)
    abc += (1).to_bytes(4, byteorder=BO)
    orig_pointer += 4
    abc += data[orig_pointer:orig_pointer+12]
    orig_img_pointer = ifb(abc[-12:-8])
    list_len = len(abc)
    abc[-12:-8] = list_len.to_bytes(4, byteorder=BO)
    new_img_pointer = len(abc)
    abc += data[orig_img_pointer:orig_img_pointer+500000]
    abc[24:28] = (len(abc) - len(data)).to_bytes(4, byteorder=BO)
    data = bytes(abc)
    print(len(data))
    print(int.from_bytes(data[20:24], BO))
    header = ACSHeader(data, 0)
    character = ACSCharacterInfo(data, header.loc_acscharacter.offset)
    print(header.loc_acsimage.offset)
    image_infos = ACSList(data, header.loc_acsimage.offset, 4, ACSImageInfo)
    images = []
    print("huiiiiiiiiiiiii", image_infos.elems[-1].loc.offset)
    print(len(image_infos.elems))
    for i in image_infos.elems[::-1]:
        print(i.loc.size)
        img = ACSImage(data, i.loc.offset)
        images.append(img)
        with open('test.acs', 'wb') as of:
            abc = bytearray(data)
            x = character.palette_offset + 6 + 254 * 4
            #abc[5500000:5600000] = abc[character.palette_offset:character.palette_offset+1000000]
            print(int.from_bytes(abc[5246218:5246218+4], BO))
            linfo = 5249423 + 2 + 2
            bonzi_str = ACSString(abc, linfo)
            linfo = linfo + bonzi_str.total_len()+2
            where_the_palette_should_be = linfo + 6
            print(f"where_the_palette_should_be: {where_the_palette_should_be}")
            print(f"x: {x}")
            diff = where_the_palette_should_be - x - 2 - 100*4
            #abc[5249423-diff:5249423-diff+372] = abc[5249423:5249423+372]

            print("IMAAAAAAAGE\n\n\n")
            image_orig_offset = new_img_pointer
            print(abc[image_orig_offset+1])
            abc[image_orig_offset+2] = 10
            print(ifb(abc[image_orig_offset+1:image_orig_offset+3]))
            image_orig_offset = new_img_pointer + 2
            print(abc[image_orig_offset+1])
            abc[image_orig_offset+2] = 10
            print(ifb(abc[image_orig_offset+1:image_orig_offset+3]))


            # change the background color to use color 129 from the palette
            #abc[4743033 + 4 + 6 + 1] = 0x02
            #compd = b'\x00@\x00\x04\x10\xd0\x90\x80B\xed\x98\x01\xb7\xff\xff\xff\xff\xff\xff'
            #compd = b'\x00@\x00\x04\x10\xd0\x90\x80B\xed\x98\x01\xb7\xfb\x80\xbf\xff\xff\xff\xff\xff\xff'
            #compd = b'\x00@\x00\x04\x10\xd0\x90\x80B\xed\x98\x01\xb7\xfb\x83\xff\xfd\xff\xff\xff\xff\xff\xff'
            compd = b'\x00@\x00\x04\x10\xd0\x90\x80B\xed\x98\x01\xb7\xfb\x9f\xff\xfb\xff\xff\xff\xff\xff\xff'
            for (ind, dat) in enumerate(compd):
                abc[new_img_pointer + 4 + 6 + ind] = dat
                print(abc[new_img_pointer + 4 + 6 + ind])
            abc[header.loc_acscharacter.offset + 32] = 129
            print(diff)
            print(abc[linfo:linfo+20])
            print(ifb(abc[linfo:linfo+4]))
            print(linfo)
            bonzi_str = ACSString(abc, linfo)
            print(x)
            print(abc[x:x+4])
            # overwrite palette
            for ind in range(256):
                x = character.palette_offset + 6 + ind * 4
                abc[x] = 255-ind
                abc[x+1] = 255-ind
                abc[x+2] = 255-ind
            img = ACSImage(bytes(abc), i.loc.offset)
            of.write(bytes(abc))
        break

asd = None
with open('bonzitest.txt', 'r') as f:
    asd = f.read()
asd = asd.replace("\n","").replace(" ","")
if len(asd) % 8 != 0:
    asd += '1' * (8 - (len(asd) % 8))
binstr = bitstring.BitArray(bin=asd)
print(bitstream_to_bytes(binstr, 0, len(asd)))
print("wtf")

#'''
if __name__ == '__main__':
    with open('bonz.acs', 'rb') as f:
        parse(f.read())
'''
x = """   00 40 00 04 10 D0 90 80
    42 ED 98 01 B7 FF FF FF
    FF FF FF"""
b = bytearray(b'')
for c in x.strip().split():
    print(int(c, 16))
    b.append(int(c, 16))
print(bytes(b))
out = decompress(b)
print(["%02x" % x for x in out[:100]])
#'''
