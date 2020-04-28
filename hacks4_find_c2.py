import os
import types 
import datetime
import json

time_stamp = datetime.datetime.now()
mainichi_dir = time_stamp.strftime('%Y-%m-%d') 

def int_my(s):

    if s not in ["a", "b", "c", "d", "e", "f"]:
        return int(s)        
    else:
        if s == "a":
            return 10
        elif s == "b":
            return 11
        elif s == "c":
            return 12
        elif s == "d":
            return 13
        elif s == "e":
            return 14
        else:
            return 15

def get_variable_address(file, variable):

    cmd = "objdump -t " + file + " | grep " + variable + "$"
    # print "get_variable_address_cmd: " + cmd

    result = os.popen(cmd)
    result_str = result.read().strip()
    
    # print result_str
    return result_str

def check_section_exists(file, section):

    cmd = "objdump -h " + file + " | grep " + section
    r = os.popen(cmd)
    r_s = r.read().strip()
    if len(r_s) > 0:
        return True
    else:
        return False

def process_data_section(file, base):

    data_exists = check_section_exists(file, "\\\\.data")
    sdata_exists = check_section_exists(file, "\\\\.sdata")

    result_str = ""
    if data_exists:

        data_cmd = "greadelf -x .data " + file + " | grep " + base
        # print "data_cmd: " + cmd
        result_data = os.popen(data_cmd)
        result_str = result_data.read().strip()

        if len(result_str) == 0:
            if sdata_exists:
                sdata_cmd = "greadelf -x .sdata " + file + " | grep " + base
                result_sdata = os.popen(sdata_cmd)
                result_str = result_sdata.read().strip()

    return result_str

def msb_2_lsb(msb_str):
    
    a = ""
    for i in range(len(msb_str)-1, -1, -2):
        b = msb_str[i-1] + msb_str[i]
        a += b

    return a

def find_desired_data_raw_msb(data_section_result, offset, size):

    split = data_section_result.split()
    split_string = ""
    for i in range(1,5):
        lsbed = msb_2_lsb(split[i])
        split_string += lsbed
    
    start = 2 * offset
    end = start + size
    hex_result = split_string[start:end]
    # print "desired_data_raw: " + hex_result
    return hex_result

def find_desired_data_raw_lsb(data_section_result, offset, size):

    split = data_section_result.split()
    split_string = ""
    for i in range(1,5):
        split_string += split[i]
    
    start = 2 * offset
    end = start + size
    hex_result = split_string[start:end]
    # print "desired_data_raw: " + hex_result
    return hex_result

def get_base_offset(file):

    cmd = "greadelf -x .data " + file + " | head -n 3 | tail -n 1"
    r = os.popen(cmd)
    s = r.read().strip().split()

    return int_my(s[0][-1])

def analyse_objdump(file, objdump_result):

    split = objdump_result.split()
    s = split[0]

    l = []
    for i in range(0,(len(s)/2)):
        a = s[2*i] + s[2*i+1]
        l.append(a)

    result_dict = {} 

    base_offset = get_base_offset(file)
    # print base_offset

    base = s[0:-1]
    base += str(hex(base_offset)).replace("0x", "")   
    result_dict["base"] = base

    if int_my(l[-1][1]) is not base_offset:

        if int_my(l[-1][1]) > base_offset:
            result_dict["offset"] = int_my(l[-1][1]) - get_base_offset(file)

        if int_my(l[-1][1]) < base_offset:
            # print "bingo"
            result_dict["offset"] = 16 - (base_offset - int_my(l[-1][1]))
            w = hex(int(s, 16) - 16).replace("0x", "")
            base = w[0:-1]
            base += str(hex(base_offset)).replace("0x", "")   
            result_dict["base"] = base

    else:
        result_dict["offset"] = 0

    size = "0x" + split[4]
    result_dict["size"] = int(size,16)

    x = result_dict["base"]
    y = x[-8:-1]
    result_dict["base"] = y
   
    # print "data_search_base: " + result_dict["base"]
    # print "data_search_offset: " + str(result_dict["offset"])
    # print "data_search_size: " + str(result_dict["size"])

    return result_dict

def get_int(hex_string):

    l = list(bytearray.fromhex(hex_string))
    l_r = list(reversed(l))
    l_new = []
    hex_str = ""
    for i in l_r:
        if i is not 0:
            l_new.append(i)
            hex_str += str(hex(i)).replace("0x", "")
    intager = 0
    for i in range(0, len(hex_str)):
        intager += int_my(hex_str[i]) * (16 ** (len(hex_str) - 1 - i))
    
    # print "desired_data_int: " + str(intager)
    return intager

def check_endian(file):

    r = os.popen("file " + file)
    split = r.read().strip().split()
    for i in split:
        if "SB" in i:
            return i

def get_file_names_in_dir(path):

    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for file in onlyfiles:
        if file == ".DS_Store":
            onlyfiles.remove(file)

    return onlyfiles

def main():

    now_path = os.getcwd()

    path = mainichi_dir + "/hacks4"
    onlyfiles = get_file_names_in_dir(path)
    os.chdir(path)

    c2_all = {}

    for file in onlyfiles:
        c2_file_betsu = {}

        endian = check_endian(file)

        for search_string in ["hacks", "hacks3", "hacks2", "hacks4", "_bp"]:

            # print "*" * 6 + " For file " + file + " and " + search_string + " *" * 6
            objdump_result = get_variable_address(file, search_string)
            r = analyse_objdump(file, objdump_result)

            r_data = process_data_section(file, r["base"])
            if len(r_data) == 0:
                print "ERROR: " + file + " " + search_string 
                c2_file_betsu[search_string] = "ERROR"
            else:

                if endian == "LSB":
                    desired_data_raw = find_desired_data_raw_lsb(r_data, r["offset"], r["size"])

                if endian == "MSB":
                    desired_data_raw = find_desired_data_raw_msb(r_data, r["offset"], r["size"])
                    
                result = get_int(desired_data_raw)
                c2_file_betsu[search_string] = result

        c2_str = str(c2_file_betsu["hacks"]) + "." + str(c2_file_betsu["hacks2"]) + "." + str(c2_file_betsu["hacks3"]) + "." + str(c2_file_betsu["hacks4"]) + ":" + str(c2_file_betsu["_bp"])
        # print "For file " + file + ": c2: " + c2_str

        if c2_str not in c2_all.keys():
            c2_all[c2_str] = []
        
        if file not in c2_all[c2_str]:
            c2_all[c2_str].append(file)

    print c2_all
    print c2_all.keys()

    os.chdir(now_path)

    json_name = "c2/hacks4/" + mainichi_dir + ".json"
    with open(json_name, "w") as jf:
        json.dump(c2_all, jf)
    list_name = "c2/hacks4/c2_list.txt"
    with open(list_name, "a") as lf:
        for key in c2_all.keys():
            lf.write(key)
            lf.write("\n")

if __name__ == "__main__":

    main()

