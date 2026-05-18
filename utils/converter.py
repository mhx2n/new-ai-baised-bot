def dec_to_gray(n):
    return bin(n ^ (n >> 1))[2:]

def gray_to_dec(gray_str):
    n = int(gray_str, 2)
    mask = n >> 1
    while mask != 0:
        n = n ^ mask
        mask = mask >> 1
    return n

def dec_to_excess3(n):
    res = ""
    for d in str(n):
        res += f"{(int(d) + 3):04b}"
    return res

def excess3_to_dec(e3_str):
    cleaned = e3_str.replace(" ", "")
    chunks = [cleaned[i:i+4] for i in range(0, len(cleaned), 4)]
    dec_str = ""
    for c in chunks:
        if len(c) == 4:
            dec_str += str(int(c, 2) - 3)
    return int(dec_str)

def convert_all(value_str, from_base):
    try:
        if from_base == "dec": decimal_val = int(value_str)
        elif from_base == "bin": decimal_val = int(value_str, 2)
        elif from_base == "oct": decimal_val = int(value_str, 8)
        elif from_base == "hex": decimal_val = int(value_str, 16)
        elif from_base == "gray": decimal_val = gray_to_dec(value_str)
        elif from_base == "excess3": decimal_val = excess3_to_dec(value_str)
        else: return "Error: Unrecognized base option."

        if decimal_val < 0: 
            return "Error: Negative values are not supported in this module."

        res_bin = bin(decimal_val)[2:]
        res_oct = oct(decimal_val)[2:]
        res_hex = hex(decimal_val)[2:].upper()
        res_gray = dec_to_gray(decimal_val)
        res_e3 = dec_to_excess3(decimal_val)

        return (
            f"**Base Conversion Results**\n"
            f"Input Value: `{value_str}` (Base: {from_base.upper()})\n\n"
            f"• Decimal: `{decimal_val}`\n"
            f"• Binary: `{res_bin}`\n"
            f"• Octal: `{res_oct}`\n"
            f"• Hexadecimal: `{res_hex}`\n"
            f"• Gray Code: `{res_gray}`\n"
            f"• Excess-3: `{res_e3}`"
        )
    except Exception:
        return f"Error: Invalid value or format provided for base {from_base.upper()}."
