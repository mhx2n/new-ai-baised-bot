def float_to_dec(val_str, base):
    if '.' not in val_str: return int(val_str, base)
    whole, frac = val_str.split('.')
    dec_val = int(whole, base) if whole else 0
    for i, digit in enumerate(frac):
        if digit.upper() in 'ABCDEF': val = ord(digit.upper()) - 55
        else: val = int(digit)
        dec_val += val * (base ** -(i + 1))
    return dec_val

def dec_to_base_float(n, base, precision=5):
    whole = int(n)
    frac = n - whole
    if base == 2: res_whole = bin(whole)[2:]
    elif base == 8: res_whole = oct(whole)[2:]
    elif base == 16: res_whole = hex(whole)[2:].upper()
    else: return str(n)
    if frac == 0: return res_whole
    res_frac = "."
    while frac > 0 and len(res_frac) <= precision + 1:
        frac *= base
        digit = int(frac)
        if base == 16: res_frac += hex(digit)[2:].upper()
        else: res_frac += str(digit)
        frac -= digit
    return res_whole + res_frac

def dec_to_gray(n): return bin(n ^ (n >> 1))[2:]
def dec_to_excess3(n): return "".join([f"{(int(d) + 3):04b}" for d in str(n) if d.isdigit()])
def dec_to_bcd(n): return " ".join([f"{int(d):04b}" for d in str(n) if d.isdigit()])
def str_to_ascii(s): return " ".join([str(ord(c)) for c in s])

def get_explanation(value_str, from_base, decimal_val, is_float):
    return (
        "\n\n💡 **Step-by-Step Explanation:**\n"
        f"• The {from_base.upper()} value `{value_str}` was first evaluated to Base-10 Decimal: `{decimal_val}`.\n"
        "• Binary, Octal, and Hex were derived by repeated division/multiplication of the Decimal value.\n"
        "• Gray Code: Computed via XOR operation of the binary value with its 1-bit right shift.\n"
        "• BCD: Each decimal digit was converted to a 4-bit binary sequence.\n"
        "• Excess-3: Created by adding 3 to each decimal digit before converting to 4-bit binary."
    )

def convert_all(value_str, from_base):
    try:
        if from_base == "ascii":
            return f"🔢 **ASCII Conversion**\nInput: `{value_str}`\nOutput: `{str_to_ascii(value_str)}`"

        base_map = {"dec": 10, "bin": 2, "oct": 8, "hex": 16}
        if from_base not in base_map: return "❌ Error: Unsupported base."
        
        b = base_map[from_base]
        decimal_val = float_to_dec(value_str, b)
        
        if decimal_val < 0: return "❌ Error: Negative values not supported."
        is_float = '.' in value_str
        
        if is_float:
            res_bin = dec_to_base_float(decimal_val, 2)
            res_oct = dec_to_base_float(decimal_val, 8)
            res_hex = dec_to_base_float(decimal_val, 16)
            res_gray = "N/A"
            res_e3 = "N/A"
            res_bcd = "N/A"
        else:
            decimal_val = int(decimal_val)
            res_bin = bin(decimal_val)[2:]
            res_oct = oct(decimal_val)[2:]
            res_hex = hex(decimal_val)[2:].upper()
            res_gray = dec_to_gray(decimal_val)
            res_e3 = dec_to_excess3(decimal_val)
            res_bcd = dec_to_bcd(decimal_val)

        exp = get_explanation(value_str, from_base, decimal_val, is_float)

        return (
            f"🔢 **Advanced Conversion Results**\n"
            f"Input: `{value_str}` ({from_base.upper()})\n\n"
            f"🔹 **Decimal:** `{decimal_val}`\n"
            f"🔹 **Binary:** `{res_bin}`\n"
            f"🔹 **Octal:** `{res_oct}`\n"
            f"🔹 **Hexadecimal:** `{res_hex}`\n"
            f"🔹 **BCD:** `{res_bcd}`\n"
            f"🔹 **Gray Code:** `{res_gray}`\n"
            f"🔹 **Excess-3:** `{res_e3}`"
            f"{exp}"
        )
    except Exception as e:
        return f"❌ **Error:** Invalid format for {from_base.upper()}."
