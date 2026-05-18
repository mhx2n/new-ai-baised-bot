import base64
import binascii

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

def text_to_binary(text): return ' '.join(format(ord(c), '08b') for c in text)
def text_to_hex(text): return binascii.hexlify(text.encode()).decode('utf-8')
def text_to_base64(text): return base64.b64encode(text.encode()).decode('utf-8')

def convert_all(value_str, from_base):
    try:
        # Advanced Text Conversions
        if from_base == "text":
            return (
                f"🔡 **Text Conversion Results**\n"
                f"Input: `{value_str}`\n\n"
                f"🔹 **Binary:** `{text_to_binary(value_str)}`\n"
                f"🔹 **Hexadecimal:** `{text_to_hex(value_str)}`\n"
                f"🔹 **Base64:** `{text_to_base64(value_str)}`"
            )

        # Standard Number Conversions
        base_map = {"dec": 10, "bin": 2, "oct": 8, "hex": 16}
        if from_base not in base_map: return "❌ Error: Unsupported base."
        
        b = base_map[from_base]
        decimal_val = float_to_dec(value_str, b)
        if decimal_val < 0: return "❌ Error: Negative values not supported yet."
        is_float = '.' in value_str
        
        if is_float:
            res_bin = dec_to_base_float(decimal_val, 2)
            res_oct = dec_to_base_float(decimal_val, 8)
            res_hex = dec_to_base_float(decimal_val, 16)
            
            # Handling fractional BCD/Excess-3 directly from the string representation
            whole_str, frac_str = str(decimal_val).split('.')
            res_bcd = f"{dec_to_bcd(whole_str)} . {dec_to_bcd(frac_str)}"
            res_e3 = f"{dec_to_excess3(whole_str)} . {dec_to_excess3(frac_str)}"
            res_gray = "N/A (Integers Only)"
        else:
            decimal_val = int(decimal_val)
            res_bin = bin(decimal_val)[2:]
            res_oct = oct(decimal_val)[2:]
            res_hex = hex(decimal_val)[2:].upper()
            res_gray = dec_to_gray(decimal_val)
            res_e3 = dec_to_excess3(decimal_val)
            res_bcd = dec_to_bcd(decimal_val)

        exp = (
            "\n\n💡 **Detailed Explanation:**\n"
            f"1. **Decimal:** Evaluated to `{decimal_val}` (Base-10).\n"
            f"2. **Binary/Oct/Hex:** Converted from Decimal using successive division (whole) and multiplication (fractions).\n"
            f"3. **BCD:** Each decimal digit independently converted to 4-bit binary.\n"
            f"4. **Excess-3:** 3 added to each decimal digit, then converted to 4-bit.\n"
            f"5. **Gray Code:** Binary shifted right 1 bit and XORed with itself."
        )

        return (
            f"🔢 **Advanced System Conversion**\n"
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
