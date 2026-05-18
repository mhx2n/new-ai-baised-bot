def float_to_dec(val_str, base):
    if '.' not in val_str: return int(val_str, base)
    whole, frac = val_str.split('.')
    dec_val = int(whole, base) if whole else 0
    for i, digit in enumerate(frac):
        dec_val += int(digit, base) * (base ** -(i + 1))
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

def convert_all(value_str, from_base):
    try:
        # Determine numerical base
        base_map = {"dec": 10, "bin": 2, "oct": 8, "hex": 16}
        if from_base not in base_map: return "❌ Error: Unsupported base for fractional conversion."
        
        b = base_map[from_base]
        decimal_val = float_to_dec(value_str, b)
        
        # Prevent huge logic errors for negatives
        if decimal_val < 0: return "❌ Error: Negative values not supported."

        is_float = '.' in value_str
        
        if is_float:
            res_bin = dec_to_base_float(decimal_val, 2)
            res_oct = dec_to_base_float(decimal_val, 8)
            res_hex = dec_to_base_float(decimal_val, 16)
            res_gray = "N/A (Integers Only)"
            res_e3 = "N/A (Integers Only)"
        else:
            decimal_val = int(decimal_val)
            res_bin = bin(decimal_val)[2:]
            res_oct = oct(decimal_val)[2:]
            res_hex = hex(decimal_val)[2:].upper()
            res_gray = dec_to_gray(decimal_val)
            res_e3 = dec_to_excess3(decimal_val)

        return (
            f"🔢 **Advanced Conversion Results**\n"
            f"Input: `{value_str}` ({from_base.upper()})\n\n"
            f"🔹 **Decimal:** `{decimal_val}`\n"
            f"🔹 **Binary:** `{res_bin}`\n"
            f"🔹 **Octal:** `{res_oct}`\n"
            f"🔹 **Hexadecimal:** `{res_hex}`\n"
            f"🔹 **Gray Code:** `{res_gray}`\n"
            f"🔹 **Excess-3:** `{res_e3}`"
        )
    except Exception as e:
        return f"❌ **Error:** Invalid format for {from_base.upper()}.\nDetails: {str(e)[:30]}"
